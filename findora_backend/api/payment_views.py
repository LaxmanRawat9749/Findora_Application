import logging
import requests
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings

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
        
        # We need a return URL. For Android WebView interception, we use a custom scheme.
        return_url = "findorapp://payment/callback"
        
        payload = {
            "return_url": return_url,
            "website_url": "https://findora.app",
            "amount": price * 100,  # in paisa
            "purchase_order_id": str(payment.id),
            "purchase_order_name": item.title,
            "customer_info": {
                "name": request.user.username,
                "email": request.user.email or "user@findora.app",
                "phone": getattr(request.user, 'phone_number', '9800000000')
            }
        }
        
        headers = {
            "Authorization": f"key {secret_key}",
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
            logger.error(f"Khalti initiate failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Khalti Response: {e.response.text}")
            payment.status = 'FAILED'
            payment.save(update_fields=['status'])
            return Response({'error': 'Failed to initiate payment with Khalti.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
