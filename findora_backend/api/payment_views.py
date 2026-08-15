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

        return Response({
            'payment_id': payment.id,
            'amount': price,
            'amount_paisa': price * 100,
            'public_key': getattr(settings, 'KHALTI_PUBLIC_KEY', 'test_public_key'),
            'product_identity': str(item.id),
            'product_name': item.title
        }, status=status.HTTP_200_OK)


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
        payment_id = request.data.get('payment_id')
        khalti_token = request.data.get('token')

        if not payment_id or not khalti_token:
            return Response({'error': 'payment_id and token are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payment = Payment.objects.get(pk=payment_id, user=request.user)
        except Payment.DoesNotExist:
            return Response({'error': 'Payment record not found.'}, status=status.HTTP_404_NOT_FOUND)

        if payment.status == 'COMPLETED':
            return Response({'message': 'Payment already completed.'}, status=status.HTTP_200_OK)

        if payment.status != 'PENDING':
            return Response({'error': 'Payment is not in a pending state.'}, status=status.HTTP_400_BAD_REQUEST)

        secret_key = getattr(settings, 'KHALTI_SECRET_KEY', 'test_secret_key')
        
        # Verify with Khalti API (Mocking if test_secret_key)
        is_verified = False
        if secret_key == 'test_secret_key':
            is_verified = True # MOCK verification
        else:
            url = "https://khalti.com/api/v2/payment/verify/"
            payload = {
                "token": khalti_token,
                "amount": int(payment.amount * 100) # Khalti amount is in paisa
            }
            headers = {
                "Authorization": f"Key {secret_key}"
            }
            try:
                response = requests.post(url, data=payload, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    # Optionally verify amount and other details
                    if data.get('state', {}).get('name') == 'Completed':
                        is_verified = True
            except requests.exceptions.RequestException as e:
                logger.error(f"Khalti verification failed: {e}")
                return Response({'error': 'Payment verification failed due to network error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if is_verified:
            # Activate Feature
            now = timezone.now()
            hours_to_add = PROMOTION_PACKAGES[payment.promotion_duration]['hours']
            
            payment.status = 'COMPLETED'
            payment.transaction_id = khalti_token
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
