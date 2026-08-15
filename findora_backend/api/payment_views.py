import logging
import requests
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse

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

        package_info = PROMOTION_PACKAGES.get(package_key)
        if not package_info:
            return Response({'error': 'Invalid promotion package.'}, status=status.HTTP_400_BAD_REQUEST)

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
            provider='khalti',
            status='PENDING',
            promotion_duration=package_key
        )

        # Call Khalti API to generate pidx and payment_url
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
            return Response({'error': 'pidx is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(transaction_id=pidx, user=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found for this pidx.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'COMPLETED':
            return Response({'message': 'Payment already completed.'}, status=status.HTTP_200_OK)

        if payment.status != 'PENDING':
            return Response({'error': 'Payment is not in a pending state.'}, status=status.HTTP_400_BAD_REQUEST)

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
