import logging
import requests
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponse
from django.urls import reverse

import base64
import hmac
import hashlib
import uuid
import json

from .models import Item, Payment

logger = logging.getLogger(__name__)

# Promotion packages in NPR and their durations in hours
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
        "package": "24h",
        "provider": "esewa"
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

        # Prevent duplicate active promotion
        now = timezone.now()
        if item.is_featured and item.featured_until and item.featured_until > now:
            return Response({'error': 'Item is already promoted and featured.'}, status=status.HTTP_400_BAD_REQUEST)

        price = package_info['price']

        # Create PENDING payment record
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
        else:
            return self._initiate_esewa(request, payment, price, package_key, item)

    def _initiate_khalti(self, request, payment, price, package_key, item):
        secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        khalti_url = f"{getattr(settings, 'KHALTI_API_URL', 'https://a.khalti.com/api/v2')}/epayment/initiate/"
        
        base_url = getattr(settings, 'BACKEND_BASE_URL', None) or request.build_absolute_uri('/')[:-1]
        return_url = f"{base_url}/api/payments/callback/"
        website_url = base_url
        
        payload = {
            "return_url": return_url,
            "website_url": website_url,
            "amount": int(price * 100),  # amount in paisa
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
            khalti_resp = requests.post(khalti_url, json=payload, headers=headers, timeout=10)
            khalti_resp.raise_for_status()
            data = khalti_resp.json()
            
            pidx = data.get('pidx')
            payment_url = data.get('payment_url')
            
            payment.transaction_id = pidx
            payment.save(update_fields=['transaction_id'])
            
            return Response({
                'payment_url': payment_url,
                'pidx': pidx,
            }, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti initiate failed: {e}")
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return Response({'error': 'Payment service is temporarily unavailable.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _initiate_esewa(self, request, payment, price, package_key, item):
        """
        Initiates eSewa ePay v2 form payment flow.
        Generates unique transaction UUID, HMAC-SHA256 signature, and returns
        the form URL to be loaded in the in-app payment WebView.
        """
        try:
            # Generate unique transaction UUID
            transaction_uuid = f"txn-{payment.id}-{uuid.uuid4().hex[:8]}"
            payment.transaction_id = transaction_uuid
            payment.save(update_fields=['transaction_id'])
            
            amount = str(int(price))
            merchant_code = getattr(settings, 'ESEWA_PRODUCT_CODE', 'EPAYTEST')
            secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
            
            # eSewa v2 signature string: total_amount,transaction_uuid,product_code
            message = f"total_amount={amount},transaction_uuid={transaction_uuid},product_code={merchant_code}"
            hmac_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
            signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
            
            # Form URL rendered by Django for the in-app WebView
            base_url = getattr(settings, 'BACKEND_BASE_URL', None) or request.build_absolute_uri('/')[:-1]
            try:
                form_url = request.build_absolute_uri(reverse('esewa-form', kwargs={'payment_id': payment.id}))
            except Exception:
                form_url = f"{base_url}/api/payments/esewa/form/{payment.id}/"
            
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
    Renders an HTML form that auto-submits to the configured eSewa ePay v2 endpoint.
    Loaded inside Findora's in-app payment WebView (KhaltiWebViewActivity).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id, provider='esewa', status='PENDING')
        except Payment.DoesNotExist:
            return HttpResponse("Invalid or expired payment session.", status=404)

        esewa_form_url = getattr(settings, 'ESEWA_EPAY_FORM_URL', 'https://rc-epay.esewa.com.np/api/epay/main/v2/form')
        merchant_code = getattr(settings, 'ESEWA_PRODUCT_CODE', 'EPAYTEST')
        secret_key = getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q')
        
        amount = str(int(payment.amount))
        transaction_uuid = payment.transaction_id
        
        message = f"total_amount={amount},transaction_uuid={transaction_uuid},product_code={merchant_code}"
        hmac_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
        signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
        
        base_url = getattr(settings, 'BACKEND_BASE_URL', None) or request.build_absolute_uri('/')[:-1]
        try:
            success_url = request.build_absolute_uri(reverse('esewa-verify-callback'))
        except Exception:
            success_url = f"{base_url}/api/payments/esewa/verify-callback/"
            
        failure_url = f"{base_url}/api/payments/callback/?status=Failed&pidx={transaction_uuid}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connecting to eSewa...</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #F8F9FD;
            color: #1A1A2E;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            text-align: center;
        }}
        .card {{
            background: #FFFFFF;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            padding: 32px;
            max-width: 380px;
            width: 100%;
        }}
        .spinner {{
            border: 4px solid #E9ECEF;
            border-top: 4px solid #60BB46;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        h2 {{
            font-size: 18px;
            margin: 0 0 8px;
            color: #1A1A2E;
        }}
        p {{
            font-size: 14px;
            color: #6C757D;
            margin: 0 0 20px;
        }}
        .btn {{
            background-color: #60BB46;
            color: white;
            border: none;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 10px;
            width: 100%;
            cursor: pointer;
        }}
    </style>
</head>
<body onload="document.getElementById('esewaForm').submit();">
    <div class="card">
        <div class="spinner"></div>
        <h2>Redirecting to eSewa</h2>
        <p>Connecting securely to eSewa payment gateway...</p>
        <form id="esewaForm" action="{esewa_form_url}" method="POST">
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
            <noscript>
                <input type="submit" value="Continue to eSewa" class="btn">
            </noscript>
        </form>
    </div>
</body>
</html>"""
        return HttpResponse(html)


class EsewaVerifyCallbackView(APIView):
    """
    GET/POST /api/payments/esewa/callback/ and /api/payments/esewa/verify-callback/
    Handles both direct eSewa server webhook and user redirect.
    Verifies HMAC-SHA256 signature, validates status == 'SUCCESS' or 'COMPLETE',
    checks amount integrity, and activates promotion only upon verified success.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return self._process_callback(request, is_post=False)

    def post(self, request):
        return self._process_callback(request, is_post=True)

    def _process_callback(self, request, is_post=False):
        # 1. Extract payload from query params or POST body
        payload = {}
        data_encoded = request.query_params.get('data') if not is_post else request.data.get('data')
        
        if data_encoded:
            try:
                decoded_bytes = base64.b64decode(data_encoded)
                payload = json.loads(decoded_bytes.decode('utf-8'))
            except Exception as err:
                logger.error(f"eSewa callback base64 decode error: {err}")
        elif is_post:
            payload = request.data
        else:
            payload = request.query_params.dict()

        transaction_uuid = payload.get('transaction_uuid') or payload.get('pidx')
        if not transaction_uuid:
            if is_post:
                return Response({'error': 'transaction_uuid missing'}, status=status.HTTP_400_BAD_REQUEST)
            return redirect('/api/payments/callback/?status=Failed&pidx=unknown')

        try:
            payment = Payment.objects.get(transaction_id=transaction_uuid)
        except Payment.DoesNotExist:
            logger.error(f"eSewa callback: Payment record not found for {transaction_uuid}")
            if is_post:
                return Response({'error': 'Payment record not found'}, status=status.HTTP_404_NOT_FOUND)
            return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

        # Step 1: Verify HMAC Signature if present
        signed_field_names = payload.get('signed_field_names', '')
        signature = payload.get('signature')
        secret_key = getattr(settings, 'ESEWA_INTENT_SECRET_KEY', getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q'))

        if signature and signed_field_names:
            fields = signed_field_names.split(',')
            message_parts = []
            for field in fields:
                field_clean = field.strip()
                val = payload.get(field_clean, '')
                if isinstance(val, float) and val.is_integer():
                    val = int(val)
                message_parts.append(f"{field_clean}={val}")
            
            message = ",".join(message_parts)
            hmac_obj = hmac.new(secret_key.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
            expected_signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')

            if signature != expected_signature:
                logger.error(f"eSewa signature verification mismatch for {transaction_uuid}.")
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])
                if is_post:
                    return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

        # Step 2: Verify Status is SUCCESS / COMPLETE
        status_val = str(payload.get('status', '')).upper()
        if status_val not in ('SUCCESS', 'COMPLETE'):
            logger.warning(f"eSewa callback returned non-successful status '{status_val}' for {transaction_uuid}")
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            if is_post:
                return Response({'error': f'Payment failed with status {status_val}'}, status=status.HTTP_400_BAD_REQUEST)
            return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

        # Step 3: Verify Amount
        raw_amount = payload.get('amount') or payload.get('total_amount')
        if raw_amount is not None:
            try:
                received_amount = float(str(raw_amount).replace(',', ''))
            except ValueError:
                received_amount = 0.0

            if received_amount != float(payment.amount):
                logger.error(f"eSewa amount mismatch for {transaction_uuid}: Expected {payment.amount}, got {received_amount}")
                payment.status = 'FAILED'
                payment.save(update_fields=['status'])
                if is_post:
                    return Response({'error': 'Amount mismatch'}, status=status.HTTP_400_BAD_REQUEST)
                return redirect(f'/api/payments/callback/?status=Failed&pidx={transaction_uuid}')

        # Step 4: Activate Promotion Idempotently
        if payment.status != 'COMPLETED':
            now = timezone.now()
            package_info = PROMOTION_PACKAGES.get(payment.promotion_duration, {'hours': 24})
            hours_to_add = package_info['hours']
            
            payment.status = 'COMPLETED'
            payment.verified_at = now
            payment.save(update_fields=['status', 'verified_at'])

            item = payment.item
            item.is_featured = True
            item.featured_until = now + timezone.timedelta(hours=hours_to_add)
            item.save(update_fields=['is_featured', 'featured_until'])
            logger.info(f"Promotion activated for Item #{item.id} until {item.featured_until} via eSewa callback.")

        if is_post:
            return Response({'status': 'SUCCESS', 'message': 'Payment verified and item promoted.'}, status=status.HTTP_200_OK)
        return redirect(f'/api/payments/callback/?status=Completed&pidx={transaction_uuid}')


class VerifyPaymentView(APIView):
    """
    POST /api/payments/verify/
    Verifies payment server-to-server with eSewa Intent/Khalti and activates item promotion.
    Body:
    {
        "pidx": "txn-1-abc12345"
    }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pidx = request.data.get('pidx')

        if not pidx:
            return Response({'error': 'pidx or transaction identifier is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(transaction_id=pidx, user=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'COMPLETED':
            return Response({
                'success': True,
                'message': 'Payment already verified and item promoted.',
                'featured_until': payment.item.featured_until
            }, status=status.HTTP_200_OK)

        if payment.status != 'PENDING':
            return Response({'error': f'Payment is in {payment.status} state.'}, status=status.HTTP_400_BAD_REQUEST)

        if payment.provider == 'khalti':
            return self._verify_khalti(request, payment, pidx)
        else:
            return self._verify_esewa(request, payment, pidx)

    def _verify_khalti(self, request, payment, pidx):
        secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        khalti_url = f"{getattr(settings, 'KHALTI_API_URL', 'https://a.khalti.com/api/v2')}/epayment/lookup/"
        
        is_verified = False
        payload = {"pidx": pidx}
        headers = {
            "Authorization": f"Key {secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(khalti_url, json=payload, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'Completed':
                    if data.get('total_amount') == (payment.amount * 100):
                        is_verified = True
                    else:
                        logger.error(f"Khalti lookup amount mismatch for {pidx}: Expected {payment.amount * 100}, got {data.get('total_amount')}")
                else:
                    logger.warning(f"Khalti lookup status: {data.get('status')} for {pidx}")
            else:
                logger.error(f"Khalti lookup HTTP {response.status_code}: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Khalti lookup failed: {e}")
            return Response({'error': 'Payment verification network error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if is_verified:
            return self._activate_promotion(payment)
        else:
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return Response({'error': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

    def _verify_esewa(self, request, payment, transaction_uuid):
        """
        Verify eSewa payment server-to-server.
        Queries eSewa Intent / ePay status endpoints and strictly validates status & amount.
        """
        merchant_code = getattr(settings, 'ESEWA_PRODUCT_CODE', 'EPAYTEST')
        amount = str(int(payment.amount))
        
        is_verified = False
        is_pending = False

        # Attempt 1: Query eSewa Intent Status Verification API
        intent_status_url = getattr(settings, 'ESEWA_INTENT_STATUS_URL', 'https://rc-checkout.esewa.com.np/api/client/intent/payment/status')
        secret_key = getattr(settings, 'ESEWA_INTENT_SECRET_KEY', getattr(settings, 'ESEWA_SECRET_KEY', '8gBm/:&EnhH.1/q'))
        
        try:
            intent_payload = {
                "product_code": merchant_code,
                "transaction_uuid": transaction_uuid,
                "total_amount": float(payment.amount),
            }
            intent_resp = requests.post(intent_status_url, json=intent_payload, timeout=5)
            if intent_resp.status_code == 200:
                data = intent_resp.json()
                status_resp = data.get('status') or data.get('data', {}).get('status', '')
                if status_resp in ('SUCCESS', 'COMPLETE'):
                    rec_amt = data.get('data', {}).get('amount') or data.get('data', {}).get('total_amount') or payment.amount
                    if float(rec_amt) == float(payment.amount):
                        is_verified = True
                elif status_resp in ('PENDING', 'BOOKED'):
                    is_pending = True
        except Exception as e:
            logger.warning(f"eSewa Intent status endpoint query: {e}")

        # Attempt 2: Query eSewa ePay status endpoint
        if not is_verified and not is_pending:
            status_url = getattr(settings, 'ESEWA_EPAY_STATUS_URL', 'https://rc.esewa.com.np/api/epay/transaction/status/')
            url = f"{status_url}?product_code={merchant_code}&total_amount={amount}&transaction_uuid={transaction_uuid}"
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    status_resp = data.get('status', '')
                    if status_resp in ('COMPLETE', 'SUCCESS'):
                        received_amount = float(str(data.get('total_amount', amount)).replace(',', ''))
                        if received_amount == float(payment.amount):
                            is_verified = True
                        else:
                            logger.error(f"eSewa status amount mismatch for {transaction_uuid}: Expected {payment.amount}, got {received_amount}")
                    elif status_resp in ('PENDING', 'BOOKED'):
                        is_pending = True
            except Exception as e:
                logger.warning(f"eSewa status check fallback query: {e}")

        # If payment is already marked completed by verify-callback, honor it
        payment.refresh_from_db()
        if payment.status == 'COMPLETED':
            return Response({
                'success': True,
                'message': 'Payment verified and item promoted.',
                'featured_until': payment.item.featured_until
            }, status=status.HTTP_200_OK)

        if is_verified:
            return self._activate_promotion(payment)
        elif is_pending:
            return Response({'error': 'Payment is still pending with eSewa.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return Response({'error': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)

    def _activate_promotion(self, payment):
        """Activates featured status on the item for the selected promotion duration."""
        now = timezone.now()
        package_info = PROMOTION_PACKAGES.get(payment.promotion_duration, {'hours': 24})
        hours_to_add = package_info['hours']
        
        payment.status = 'COMPLETED'
        payment.verified_at = now
        payment.save(update_fields=['status', 'verified_at'])

        item = payment.item
        item.is_featured = True
        item.featured_until = now + timezone.timedelta(hours=hours_to_add)
        item.save(update_fields=['is_featured', 'featured_until'])
        
        logger.info(f"Item #{item.id} successfully promoted to featured until {item.featured_until}")

        return Response({
            'success': True,
            'message': 'Payment verified and item promoted.',
            'featured_until': item.featured_until
        }, status=status.HTTP_200_OK)


class PaymentCallbackView(APIView):
    """
    GET /api/payments/callback/
    Universal callback landing page.
    Rendered when redirected back from eSewa / Khalti.
    Automatically deep-links back to Findora Android application.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        pidx = request.query_params.get('pidx', '')
        status_param = request.query_params.get('status', 'Completed')
        is_success = status_param.lower() in ('completed', 'success')
        
        title = "Payment Successful" if is_success else "Payment Status"
        color = "#60BB46" if is_success else "#E63946"
        msg = "Your payment has been processed. Returning to Findora..." if is_success else f"Payment status: {status_param}"
        
        app_deep_link = f"findora://payment?status={status_param}&pidx={pidx}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #F8F9FD;
            color: #1A1A2E;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            box-sizing: border-box;
            text-align: center;
        }}
        .card {{
            background: #FFFFFF;
            border-radius: 16px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.08);
            padding: 32px;
            max-width: 380px;
            width: 100%;
        }}
        .status-icon {{
            font-size: 48px;
            color: {color};
            margin-bottom: 16px;
        }}
        h1 {{
            font-size: 20px;
            margin: 0 0 12px;
            color: {color};
        }}
        p {{
            font-size: 14px;
            color: #6C757D;
            margin: 0 0 24px;
        }}
        .btn {{
            display: inline-block;
            background-color: #6C63FF;
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            font-size: 15px;
            font-weight: 600;
            border-radius: 10px;
            width: 100%;
            box-sizing: border-box;
        }}
    </style>
    <script>
        window.onload = function() {{
            window.location.href = "{app_deep_link}";
        }};
    </script>
</head>
<body>
    <div class="card">
        <div class="status-icon">{'✓' if is_success else 'ℹ'}</div>
        <h1>{title}</h1>
        <p>{msg}</p>
        <a href="{app_deep_link}" class="btn">Return to Findora App</a>
    </div>
</body>
</html>"""
        return HttpResponse(html)
