import logging
import requests
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse

import base64
import hmac
import hashlib
import uuid
import json

from .models import Item, Payment

logger = logging.getLogger(__name__)

# Prices defined on the backend (in NPR)
PROMOTION_PACKAGES = {
    '24h': {'price': 50, 'hours': 24},
    '3d': {'price': 100, 'hours': 72},
    '7d': {'price': 200, 'hours': 168},
}

class InitiatePaymentView(APIView):
    """
    POST /api/payments/initiate/
    Initiate a payment for promoting an item.
    Body:
    {
        "item_id": 1,
        "package": "24h"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        package_key = request.data.get('package')

        if not item_id or not package_key:
            return Response({'error': 'item_id and package are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        if item.user != request.user:
            return Response({'error': 'You can only promote your own items.'}, status=status.HTTP_403_FORBIDDEN)

        if item.type != 'lost':
            return Response({'error': 'Only lost items can be promoted.'}, status=status.HTTP_400_BAD_REQUEST)

        package_info = PROMOTION_PACKAGES.get(package_key)
        if not package_info:
            return Response({'error': 'Invalid promotion package.'}, status=status.HTTP_400_BAD_REQUEST)
            
        provider = request.data.get('provider', 'esewa').lower()
        if provider != 'esewa':
            return Response({'error': 'Only eSewa is supported for item promotion.'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if already active featured
        now = timezone.now()
        if item.is_featured and item.featured_until and item.featured_until > now:
            return Response({'error': 'Item is already featured.'}, status=status.HTTP_400_BAD_REQUEST)

        price = package_info['price']

        # Create PENDING payment
        payment = Payment.objects.create(
            user=request.user,
            item=item,
            amount=price,
            currency='NPR',
            provider=provider,
            status='PENDING',
            promotion_duration=package_key
        )

        if provider == 'khalti':
            return self._initiate_khalti(request, payment, price, package_key, item)
        elif provider == 'esewa':
            return self._initiate_esewa(request, payment, price, package_key, item)

    def _initiate_khalti(self, request, payment, price, package_key, item):
        secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        khalti_url = f"{getattr(settings, 'KHALTI_API_URL', 'https://a.khalti.com/api/v2')}/epayment/initiate/"
        # We need a return URL handled by Django
        return_url = request.build_absolute_uri('/api/payments/callback/')
        
        # Ensure the website_url matches the environment
        website_url = "https://findora-application.onrender.com" if not getattr(settings, 'DEBUG', True) else "http://127.0.0.1:8000"
        
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": int(price * 100),  # strictly an integer in paisa
            "purchase_order_id": str(payment.id),
            "purchase_order_name": item.title,
            "customer_info": {
                "name": request.user.username or "Findora User",
                "email": request.user.email or "user@findora.app",
                "phone": getattr(request.user, 'phone_number', '9800000000') or "9800000000"
            }
        }
        
        headers = {
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            khalti_resp = requests.post(khalti_url, json=payload, headers=headers)
            khalti_resp.raise_for_status()
            data = khalti_resp.json()
            
            pidx = data.get('pidx')
            payment_url = data.get('payment_url')
            
            # Save pidx to transaction_id temporarily
            payment.transaction_id = pidx
            payment.save(update_fields=['transaction_id'])
            
            return Response({
                'payment_url': payment_url,
                'pidx': pidx,
            }, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            payment_env = getattr(settings, 'PAYMENT_ENV', 'test')
            khalti_status = khalti_resp.status_code if 'khalti_resp' in locals() else 'Unknown'
            khalti_body = khalti_resp.text if 'khalti_resp' in locals() else 'None'
            key_configured = bool(getattr(settings, 'KHALTI_SECRET_KEY', None) and getattr(settings, 'KHALTI_SECRET_KEY') != 'test_secret_key')
            
            logger.error(
                f"KHALTI INITIATE DIAGNOSTIC:\n"
                f"Endpoint: {khalti_url}\n"
                f"HTTP Status: {khalti_status}\n"
                f"Response Body: {khalti_body}\n"
                f"Exception: {str(e)}\n"
                f"Package: {package_key}\n"
                f"Amount (Paisa): {price * 100}\n"
                f"Environment: {payment_env}\n"
                f"KHALTI_SECRET_KEY configured: {key_configured}"
            )
            
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            
            error_msg = "Payment service is temporarily unavailable."
            if khalti_status == 401:
                error_msg = "Payment configuration error (Unauthorized)."
            elif khalti_status == 400:
                error_msg = "Unable to start payment. Invalid request parameters."
                
            return Response({'error': error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _initiate_esewa(self, request, payment, price, package_key, item):
        """Initiate eSewa ePay v2 form submission flow."""
        try:
            # Generate unique transaction UUID
            transaction_uuid = f"{payment.id}-{uuid.uuid4().hex[:8]}"
            payment.transaction_id = transaction_uuid
            payment.save(update_fields=['transaction_id'])
            
            amount = str(price)
            tax_amount = "0"
            total_amount = amount
            
            # Message to sign
            # For eSewa v2: total_amount,transaction_uuid,product_code
            merchant_code = getattr(settings, 'ESEWA_MERCHANT_ID', 'EPAYTEST')
            secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
            
            message = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={merchant_code}"
            
            # Create HMAC SHA256 signature
            hmac_obj = hmac.new(
                secret_key.encode('utf-8'),
                message.encode('utf-8'),
                hashlib.sha256
            )
            signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
            
            # We return a URL to a new Django view that will render the auto-submitting form
            form_url = request.build_absolute_uri(reverse('esewa-form', kwargs={'payment_id': payment.id}))
            
            return Response({
                'payment_url': form_url,
                'pidx': transaction_uuid,
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"eSewa initiate failed: {e}")
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return Response({'error': 'Failed to initiate payment with eSewa.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class EsewaFormView(APIView):
    """
    GET /api/payments/esewa/form/<payment_id>/
    Renders an HTML form that auto-submits to eSewa ePay v2 endpoint.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, provider='esewa', status='PENDING')
        except Payment.DoesNotExist:
            return HttpResponse("Invalid payment session.", status=404)
            
        payment_env = getattr(settings, 'PAYMENT_ENV', 'test')
        if payment_env == 'live':
            esewa_url = "https://epay.esewa.com.np/api/epay/main/v2/form"
        else:
            esewa_url = "https://rc-epay.esewa.com.np/api/epay/main/v2/form"
            
        merchant_code = getattr(settings, 'ESEWA_MERCHANT_ID', 'EPAYTEST')
        secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
        
        amount = str(int(payment.amount))
        transaction_uuid = payment.transaction_id
        
        message = f"total_amount={amount},transaction_uuid={transaction_uuid},product_code={merchant_code}"
        hmac_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        
        success_url = request.build_absolute_uri(f'/api/payments/esewa/verify-callback/')
        failure_url = request.build_absolute_uri(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')
        
        html = f'''
        <!DOCTYPE html>
        <html>
        <head><title>Redirecting to eSewa...</title></head>
        <body onload="document.forms[0].submit()">
            <p>Redirecting to secure payment gateway...</p>
            <form action="{esewa_url}" method="POST" style="display:none;">
                <input type="hidden" name="amount" value="{amount}">
                <input type="hidden" name="tax_amount" value="0">
                <input type="hidden" name="total_amount" value="{amount}">
                <input type="hidden" name="transaction_uuid" value="{transaction_uuid}">
                <input type="hidden" name="product_code" value="{merchant_code}">
                <input type="hidden" name="product_service_charge" value="0">
                <input type="hidden" name="product_delivery_charge" value="0">
                <input type="hidden" name="success_url" value="{success_url}">
                <input type="hidden" name="failure_url" value="{failure_url}">
                <input type="hidden" name="signed_field_names" value="total_amount,transaction_uuid,product_code">
                <input type="hidden" name="signature" value="{signature}">
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
        '''
        return HttpResponse(html)

from django.shortcuts import redirect

class EsewaVerifyCallbackView(APIView):
    """
    GET /api/payments/esewa/verify-callback/
    eSewa redirects here after payment. We decode the base64 data, verify the signature,
    and then redirect to the common callback URL that Android intercepts.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        data_encoded = request.query_params.get('data')
        if not data_encoded:
            return redirect('/api/payments/callback/?status=Failed&pidx=unknown')

        try:
            decoded_bytes = base64.b64decode(data_encoded)
            decoded_str = decoded_bytes.decode('utf-8')
            payload = json.loads(decoded_str)
            
            transaction_uuid = payload.get('transaction_uuid')
            status_val = payload.get('status')
            total_amount = str(payload.get('total_amount'))
            signed_field_names = payload.get('signed_field_names', '')
            signature = payload.get('signature')

            try:
                payment = Payment.objects.get(transaction_id=transaction_uuid)
            except Payment.DoesNotExist:
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

            # Step 1: Verify Signature
            secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
            
            fields = signed_field_names.split(',')
            message_parts = []
            for field in fields:
                # eSewa includes some fields like 'total_amount' as float in JSON but string in signature sometimes,
                # actually, we just use the exact string representation from the JSON payload or format it properly.
                # However, taking it directly from the dict is standard.
                # But wait! If eSewa sends 'total_amount': 50.0 in JSON, it was signed as '50.0' or '50'?
                # Best is to just take str() or if eSewa sends string, take it directly.
                val = payload.get(field, '')
                # If the value is a float ending in .0, eSewa often sent it as a string without .0 if originally sent like that,
                # but we'll use exactly what's parsed. We can also use request.GET directly if it was form encoded, but it's base64 json.
                # We'll use str(val) but remove .0 if it's an integer to match our "50" exactly if they passed it back differently,
                # Actually, standard eSewa docs say to use the value from the JSON.
                # Just use str(val). If val is float, it might format as "50.0".
                # Let's clean it just in case:
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                message_parts.append(f"{field}={val}")
            
            message = ",".join(message_parts)
            
            hmac_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
            expected_signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
            
            if signature != expected_signature:
                logger.error(f"eSewa signature verification failed for {transaction_uuid}. Expected {expected_signature}, got {signature}")
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

            # Step 2: Verify Status
            if status_val != 'COMPLETE':
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

            # Step 3: Verify Amount
            try:
                received_amount = float(total_amount.replace(',', ''))
            except ValueError:
                received_amount = 0.0

            if received_amount != float(payment.amount):
                logger.error(f"eSewa amount mismatch for {transaction_uuid}: Expected {payment.amount}, got {received_amount}")
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

            # If valid, activate
            if payment.status != 'COMPLETED':
                now = timezone.now()
                hours_to_add = PROMOTION_PACKAGES[payment.promotion_duration]['hours']
                
                payment.status = 'COMPLETED'
                payment.verified_at = now
                payment.save()

                item = payment.item
                item.is_featured = True
                item.featured_until = now + timezone.timedelta(hours=hours_to_add)
                item.save(update_fields=['is_featured', 'featured_until'])

            return redirect(f'/api/payments/callback/?status=Completed&pidx={transaction_uuid}')

        except Exception as e:
            logger.error(f"eSewa verify callback error: {e}")
            return redirect('/api/payments/callback/?status=Failed&pidx=unknown')


class VerifyPaymentView(APIView):
    """
    POST /api/payments/verify/
    Verify Khalti payment and activate promotion.
    Body:
    {
        "payment_id": 1,
        "token": "khalti_token"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pidx = request.data.get('pidx')

        if not pidx:
            # For eSewa, they return transaction_uuid in the callback? Wait, eSewa v2 callback URL receives ?data=base64_encoded_payload
            return Response({'error': 'pidx or transaction identifier is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # pidx is the transaction_id for both Khalti and eSewa in our DB
            payment = Payment.objects.get(transaction_id=pidx, user=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found for this identifier.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'COMPLETED':
            return Response({'message': 'Payment already completed.'}, status=status.HTTP_200_OK)

        if payment.status != 'PENDING':
            return Response({'error': 'Payment is not in a pending state.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.provider == 'khalti':
            return self._verify_khalti(request, payment, pidx)
        elif payment.provider == 'esewa':
            # eSewa passes ?data= in callback, but Android intercepts it and we just need to verify with eSewa API
            return self._verify_esewa(request, payment, pidx)

    def _verify_khalti(self, request, payment, pidx):
        secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        khalti_url = f"{getattr(settings, 'KHALTI_API_URL', 'https://a.khalti.com/api/v2')}/epayment/lookup/"
        
        is_verified = False
        payload = {
            "pidx": pidx
        }
        headers = {
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(khalti_url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                
                # Verify status is Completed
                if data.get('status') == 'Completed':
                    # Verify amount matches (in paisa)
                    if data.get('total_amount') == (payment.amount * 100):
                        is_verified = True
                    else:
                        logger.error(f"Khalti lookup amount mismatch for pidx {pidx}. Expected {payment.amount * 100}, got {data.get('total_amount')}")
                else:
                    logger.warning(f"Khalti lookup returned status {data.get('status')} for pidx {pidx}")
            else:
                logger.error(f"Khalti lookup returned status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti lookup failed: {e}")
            return Response({'error': 'Payment verification failed due to network error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if is_verified:
            # Activate Feature
            now = timezone.now()
            hours_to_add = PROMOTION_PACKAGES[payment.promotion_duration]['hours']
            
            payment.status = 'COMPLETED'
            # transaction_id is already pidx
            payment.verified_at = now
            payment.save()

            item = payment.item
            item.is_featured = True
            item.featured_until = now + timezone.timedelta(hours=hours_to_add)
            item.save(update_fields=['is_featured', 'featured_until'])

            return Response({
                'success': True,
                'message': 'Payment verified and item promoted.',
                'featured_until': item.featured_until
            }, status=status.HTTP_200_OK)
        else:
            payment.status = 'FAILED'
            payment.save()
            return Response({'error': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

    def _verify_esewa(self, request, payment, transaction_uuid):
        """Verify eSewa payment server-to-server."""
        payment_env = getattr(settings, 'PAYMENT_ENV', 'test')
        if payment_env == 'live':
            esewa_url = "https://epay.esewa.com.np/api/epay/transaction/status/"
        else:
            esewa_url = "https://rc-epay.esewa.com.np/api/epay/transaction/status/"
            
        merchant_code = getattr(settings, 'ESEWA_MERCHANT_ID', 'EPAYTEST')
        amount = str(int(payment.amount))
        
        # eSewa v2 requires total_amount, transaction_uuid, product_code in GET query
        # esewa_url += f"?product_code={merchant_code}&total_amount={amount}&transaction_uuid={transaction_uuid}"
        
        url = f"{esewa_url}?product_code={merchant_code}&total_amount={amount}&transaction_uuid={transaction_uuid}"
        
        is_verified = False
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'COMPLETE':
                    received_amount = float(str(data.get('total_amount', '0')).replace(',', ''))
                    if received_amount == float(payment.amount):
                        is_verified = True
                    else:
                        logger.error(f"eSewa lookup amount mismatch for {transaction_uuid}: Expected {payment.amount}, got {received_amount}")
                elif data.get('status') == 'PENDING':
                    logger.info(f"eSewa transaction {transaction_uuid} is PENDING.")
                    return Response({'error': 'Payment is still pending.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    logger.warning(f"eSewa lookup returned status {data.get('status')} for {transaction_uuid}")
            else:
                logger.error(f"eSewa lookup returned status code {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"eSewa lookup failed: {e}")
            return Response({'error': 'Payment verification failed due to network error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if is_verified:
            # Activate Feature
            now = timezone.now()
            hours_to_add = PROMOTION_PACKAGES[payment.promotion_duration]['hours']
            
            payment.status = 'COMPLETED'
            payment.verified_at = now
            payment.save()

            item = payment.item
            item.is_featured = True
            item.featured_until = now + timezone.timedelta(hours=hours_to_add)
            item.save(update_fields=['is_featured', 'featured_until'])

            return Response({
                'success': True,
                'message': 'Payment verified and item promoted.',
                'featured_until': item.featured_until
            }, status=status.HTTP_200_OK)
        else:
            payment.status = 'FAILED'
            payment.save()
            return Response({'error': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

class PaymentCallbackView(APIView):
    """
    GET /api/payments/callback/
    Handles the GET redirect from Khalti after payment.
    Khalti redirects to this URL with query params: pidx, transaction_id, amount, mobile, purchase_order_id, purchase_order_name, status.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pidx = request.query_params.get('pidx')
        status_param = request.query_params.get('status')
        
        # We return a simple HTML page that confirms the status.
        # However, the Android app's WebView should intercept this URL before it fully loads.
        html = f"""
        <html>
        <head><title>Khalti Payment Callback</title></head>
        <body>
            <h1>Payment Status: {status_param}</h1>
            <p>PIDX: {pidx}</p>
            <p>Please return to the application.</p>
        </body>
        </html>
        """
        return HttpResponse(html)
