"""
Findora API views.

Implements all business logic for:
  Authentication  : register, verify OTP, resend OTP, login, logout,
                    forgot/reset/change password, token refresh
  Profile         : get and update the authenticated user's profile
  Items           : list (with search/filter), create, retrieve, update, delete
  Admin           : list pending items, approve/reject items
  Claims          : submit ownership claim
  Chat            : list messages for an item, send message
  Notifications   : list notifications, mark as read
"""

from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ChatMessage, Claim, Item, Notification, OTPToken, User
from .permissions import IsAdminRole, IsOwnerOrReadOnly, IsVerifiedUser
from .serializers import (
    ChatMessageSerializer,
    ClaimSerializer,
    ItemSerializer,
    NotificationSerializer,
    ProfileUpdateSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .utils import create_otp, send_otp_email, verify_otp


# ─────────────────────────────────────────────────────────────────────────────
# Authentication Views
# ─────────────────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """
    POST /api/register/
    Register a new user account. Creates an inactive (unverified) user,
    generates an OTP, and sends it to the supplied email address.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        # Account is active so the user exists, but not verified until OTP confirmed
        user.is_active = True
        user.is_verified = False
        user.save(update_fields=['is_active', 'is_verified'])

        otp = create_otp(user, 'email_verify')
        send_otp_email(user, otp.otp_code, 'email_verify')

        return Response(
            {
                'success': True,
                'message': 'Registration successful. Please check your email for OTP.',
                'email': user.email,
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyOTPView(APIView):
    """
    POST /api/verify-otp/
    Verify a user's OTP for email verification or password reset.
    On successful email_verify, activates the user account.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp_code = request.data.get('otp', '').strip()
        purpose = request.data.get('purpose', 'email_verify')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'success': False, 'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, message = verify_otp(user, otp_code, purpose)
        if not success:
            return Response(
                {'success': False, 'error': message},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if purpose == 'email_verify':
            user.is_verified = True
            user.save(update_fields=['is_verified'])

        return Response(
            {'success': True, 'message': message, 'verified': True},
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    POST /api/resend-otp/
    Resend a new OTP to the user's email, subject to a 60-second cooldown.
    Returns a generic success message even if the email is not found (security).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        purpose = request.data.get('purpose', 'email_verify')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Generic response to prevent email enumeration
            return Response(
                {'success': True, 'message': 'If this email exists, a new OTP has been sent.'},
                status=status.HTTP_200_OK,
            )

        # Enforce 60-second cooldown between resend requests
        last_otp = OTPToken.objects.filter(user=user, purpose=purpose).order_by('-created_at').first()
        if last_otp:
            elapsed = int((timezone.now() - last_otp.created_at).total_seconds())
            if elapsed < 60:
                wait = 60 - elapsed
                return Response(
                    {
                        'success': False,
                        'error': f'Please wait {wait} seconds before requesting a new OTP.',
                        'retry_after': wait,
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

        otp = create_otp(user, purpose)
        send_otp_email(user, otp.otp_code, purpose)

        return Response(
            {'success': True, 'message': f'New OTP sent to {email}', 'expires_in': 600},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    POST /api/login/
    Authenticate a user and return JWT access + refresh tokens.

    Validation sequence:
      1. User existence check
      2. Email verification check (403 if not verified)
      3. Account lock check (423 if locked)
      4. Password check → increment/reset failed attempts
      5. Return tokens on success
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Step 2: Email verification gate
        if not user.is_verified:
            return Response(
                {
                    'error': 'Please verify your email before logging in.',
                    'email': user.email,
                    'action': 'verify',
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Step 3: Account lock gate
        if user.is_account_locked():
            time_left = max(1, int((user.locked_until - timezone.now()).total_seconds() / 60))
            return Response(
                {'error': f'Account locked. Try again after {time_left} minute(s).'},
                status=status.HTTP_423_LOCKED,
            )

        # Step 4: Password verification
        auth_user = authenticate(request, username=username, password=password)
        if not auth_user:
            user.increment_failed_attempts()
            remaining = max(0, 5 - user.failed_login_attempts)
            if remaining == 0:
                return Response(
                    {'error': 'Account locked due to too many failed attempts. Try again after 30 minutes.'},
                    status=status.HTTP_423_LOCKED,
                )
            return Response(
                {'error': f'Invalid username or password. {remaining} attempt(s) left.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Step 5: Success — reset counter, issue tokens
        auth_user.reset_failed_attempts()
        refresh = RefreshToken.for_user(auth_user)

        return Response(
            {
                'user': UserSerializer(auth_user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    POST /api/logout/
    Blacklist the supplied refresh token so it cannot be used again.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'error': 'Invalid or already blacklisted token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ForgotPasswordView(APIView):
    """
    POST /api/forgot-password/
    Send a password-reset OTP to the given email address.
    Always returns 200 regardless of whether the email exists (security).
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            otp = create_otp(user, 'password_reset')
            send_otp_email(user, otp.otp_code, 'password_reset')
        except User.DoesNotExist:
            pass  # Silent — prevents email enumeration

        return Response(
            {'success': True, 'message': 'If this email exists, an OTP has been sent.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    POST /api/reset-password/
    Reset a user's password using a valid password-reset OTP.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp_code = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if new_password != confirm_password:
            return Response(
                {'success': False, 'error': 'Passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'success': False, 'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        success, message = verify_otp(user, otp_code, 'password_reset')
        if not success:
            return Response({'success': False, 'error': message}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()

        return Response(
            {'success': True, 'message': 'Password reset successfully. Please log in with your new password.'},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """
    POST /api/change-password/
    Change the authenticated user's password.
    Requires the current password for confirmation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not request.user.check_password(current_password):
            return Response(
                {'error': 'Current password is incorrect.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {'error': 'Passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if current_password == new_password:
            return Response(
                {'error': 'New password must be different from the current password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response(
            {'message': 'Password changed successfully. Please log in again.'},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Profile Views
# ─────────────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    """
    GET  /api/profile/ — Return the authenticated user's profile.
    PUT  /api/profile/ — Update the authenticated user's non-sensitive profile fields.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = ProfileUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        if serializer.is_valid():
            serializer.save()
            return Response(UserSerializer(request.user, context={'request': request}).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# Item Views
# ─────────────────────────────────────────────────────────────────────────────

class ItemListCreateView(APIView):
    """
    GET  /api/items/           — List all approved items (with optional search/filter).
    POST /api/items/           — Report a new lost or found item (status starts as 'pending').

    Query Parameters for GET:
      ?search=<keyword>        — Full-text search on title, description, location
      ?type=lost|found         — Filter by item type
      ?category=<category>     — Filter by category
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        queryset = Item.objects.filter(status='approved').select_related('user')

        search = request.query_params.get('search', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search)
                | Q(description__icontains=search)
                | Q(location__icontains=search)
            )

        item_type = request.query_params.get('type', '').strip()
        if item_type:
            queryset = queryset.filter(type=item_type)

        category = request.query_params.get('category', '').strip()
        if category:
            queryset = queryset.filter(category=category)

        serializer = ItemSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ItemSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user, status='pending')
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemDetailView(APIView):
    """
    GET    /api/items/{id}/ — Retrieve a single item (any status, authenticated users).
    PUT    /api/items/{id}/ — Update an item (owner only).
    DELETE /api/items/{id}/ — Delete an item (owner only).
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _get_item(self, pk):
        try:
            return Item.objects.select_related('user').get(pk=pk)
        except Item.DoesNotExist:
            return None

    def get(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ItemSerializer(item, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, item)

        serializer = ItemSerializer(item, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, item)

        item.delete()
        return Response({'message': 'Item deleted successfully.'}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Admin Views
# ─────────────────────────────────────────────────────────────────────────────

class AdminItemListView(APIView):
    """
    GET /api/admin/items/
    Return all pending items awaiting admin review.
    Restricted to users with role='admin'.
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request):
        queryset = Item.objects.filter(status='pending').select_related('user').order_by('-reported_at')
        serializer = ItemSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminVerifyItemView(APIView):
    """
    POST /api/admin/items/{id}/verify/
    Approve or reject a pending item report.

    Request body: { "action": "approve" | "reject" }

    On approval:
      - Item status → 'approved'
      - Reporter receives an 'approved' notification

    On rejection:
      - Item status → 'rejected'
      - Reporter receives a 'rejected' notification
    """

    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        try:
            item = Item.objects.select_related('user').get(pk=pk)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        action = request.data.get('action', '').strip().lower()
        if action not in ('approve', 'reject'):
            return Response(
                {'error': 'Action must be "approve" or "reject".'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action == 'approve':
            item.status = 'approved'
            notification_type = 'approved'
            notification_message = (
                f'Your {item.type} item report "{item.title}" has been approved '
                f'and is now visible to other users.'
            )
        else:
            item.status = 'rejected'
            notification_type = 'rejected'
            notification_message = (
                f'Your {item.type} item report "{item.title}" was rejected by admin. '
                f'Please review our guidelines and resubmit if needed.'
            )

        item.save(update_fields=['status', 'updated_at'])

        # Notify the item reporter
        Notification.objects.create(
            user=item.user,
            type=notification_type,
            message=notification_message,
            related_item=item,
        )

        return Response(
            {'message': f'Item {action}d successfully.', 'status': item.status},
            status=status.HTTP_200_OK,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Claim Views
# ─────────────────────────────────────────────────────────────────────────────

class ClaimCreateView(APIView):
    """
    POST /api/claims/
    Submit an ownership claim on a found item.

    A user cannot claim their own item.
    Duplicate pending claims from the same user are rejected.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item')
        proof = request.data.get('proof_description', '')

        try:
            item = Item.objects.get(pk=item_id, status='approved')
        except Item.DoesNotExist:
            return Response(
                {'error': 'Item not found or not yet approved.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        if item.user == request.user:
            return Response(
                {'error': 'You cannot claim your own item.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if Claim.objects.filter(item=item, claimant=request.user, status='pending').exists():
            return Response(
                {'error': 'You already have a pending claim for this item.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        claim = Claim.objects.create(
            item=item,
            claimant=request.user,
            proof_description=proof,
        )

        # Notify the item reporter about the new claim
        Notification.objects.create(
            user=item.user,
            type='claim',
            message=(
                f'{request.user.get_full_name() or request.user.username} '
                f'has submitted a claim on your item "{item.title}".'
            ),
            related_item=item,
        )

        serializer = ClaimSerializer(claim)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ─────────────────────────────────────────────────────────────────────────────
# Chat Views
# ─────────────────────────────────────────────────────────────────────────────

class ChatListView(APIView):
    """
    GET  /api/chat/?item_id={id} — Retrieve all messages for an item conversation.
    POST /api/chat/              — Send a message to another user about an item.

    Only the sender and receiver (participants) of a conversation can read it.
    Unread messages are marked as read when the receiver fetches the conversation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages = ChatMessage.objects.filter(
            item_id=item_id,
        ).filter(
            Q(sender=request.user) | Q(receiver=request.user)
        ).select_related('sender', 'receiver', 'item')

        # Mark messages sent to this user as read
        messages.filter(receiver=request.user, is_read=False).update(is_read=True)

        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ChatMessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save(sender=request.user)

            # Notify the receiver
            Notification.objects.create(
                user=message.receiver,
                type='message',
                message=(
                    f'New message from '
                    f'{request.user.get_full_name() or request.user.username}: '
                    f'{message.message[:60]}'
                ),
                related_item=message.item,
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# Notification Views
# ─────────────────────────────────────────────────────────────────────────────

class NotificationListView(APIView):
    """
    GET /api/notifications/
    Return all notifications for the authenticated user, newest first.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = request.user.notifications.select_related('related_item').all()
        serializer = NotificationSerializer(notifications, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkNotificationReadView(APIView):
    """
    POST /api/notifications/{id}/read/
    Mark a specific notification as read.
    Users can only mark their own notifications.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response(
                {'error': 'Notification not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)
