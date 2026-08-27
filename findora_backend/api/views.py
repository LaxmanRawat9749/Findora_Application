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

import logging
import time

import re
from django.contrib.auth import authenticate
from django.db.models import Q, Max, Case, When, Value, IntegerField
from django.utils import timezone

from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    ChatMessage,
    Conversation,
    FinderRating,
    FinderReputation,
    Item,
    ItemImage,
    Notification,
    OTPToken,
    PointTransaction,
    User,
    UserBadge,
)
from .permissions import IsAdminRole, IsOwnerOrReadOnly, IsVerifiedUser
from .reputation_service import (
    award_found_report_points,
    get_or_create_reputation,
    process_successful_return_reward,
    submit_finder_rating,
)
from .serializers import (
    ChatMessageSerializer,
    ConversationSerializer,
    FinderRatingSerializer,
    FinderReputationSerializer,
    ItemSerializer,
    NotificationSerializer,
    PointTransactionSerializer,
    ProfileUpdateSerializer,
    PublicProfileSerializer,
    RateFinderRequestSerializer,
    RegisterSerializer,
    UserBadgeSerializer,
    UserSerializer,
)
from .utils import (
    create_otp,
    get_matched_found_items_query_for_owner,
    is_found_item_matched_for_owner,
    send_otp_email,
    verify_otp,
)

logger = logging.getLogger(__name__)


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
        start_ns = time.perf_counter_ns()
        username = request.data.get('username', '').strip()
        # NOTE: password is intentionally NOT logged anywhere in this method.

        logger.info("Login attempt | username=%r | client=%s",
                    username, self._client_ip(request))

        try:
            db_start = time.perf_counter_ns()
            user = User.objects.get(username=username)
            db_ms = (time.perf_counter_ns() - db_start) / 1_000_000
            logger.debug("User lookup OK | username=%r | db=%.1f ms", username, db_ms)
        except User.DoesNotExist:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning("Login failed | reason=user_not_found | username=%r | elapsed=%.1f ms",
                           username, elapsed_ms)
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # Step 2: Email verification gate
        if not user.is_verified:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning("Login failed | reason=unverified_email | username=%r | elapsed=%.1f ms",
                           username, elapsed_ms)
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
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning("Login failed | reason=account_locked | username=%r | locked_for=%d min | elapsed=%.1f ms",
                           username, time_left, elapsed_ms)
            return Response(
                {'error': f'Account locked. Try again after {time_left} minute(s).'},
                status=status.HTTP_423_LOCKED,
            )

        # Step 4: Password verification
        auth_user = authenticate(request, username=username, password=request.data.get('password', ''))
        if not auth_user:
            user.increment_failed_attempts()
            remaining = max(0, 5 - user.failed_login_attempts)
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.warning("Login failed | reason=wrong_password | username=%r | attempts_left=%d | elapsed=%.1f ms",
                           username, remaining, elapsed_ms)
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
        token_start = time.perf_counter_ns()
        refresh = RefreshToken.for_user(auth_user)
        token_ms = (time.perf_counter_ns() - token_start) / 1_000_000
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000

        logger.info("Login success | username=%r | user_id=%d | token_gen=%.1f ms | total=%.1f ms",
                    auth_user.username, auth_user.pk, token_ms, elapsed_ms)

        return Response(
            {
                'user': UserSerializer(auth_user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _client_ip(request):
        """Return the best-effort client IP from request headers."""
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


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


class ChangeUsernameView(APIView):
    """
    POST /api/change-username/
    Change the authenticated user's username.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        new_username = request.data.get('new_username', '').strip()
        confirm_username = request.data.get('confirm_username', '').strip()

        if not new_username:
            return Response(
                {'error': 'Username cannot be empty.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_username) < 3:
            return Response(
                {'error': 'Username must be at least 3 characters long.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(new_username) > 30:
            return Response(
                {'error': 'Username must not exceed 30 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not re.match(r'^[a-zA-Z0-9_]+$', new_username):
            return Response(
                {'error': 'Username can only contain letters, numbers, and underscores.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_username != confirm_username:
            return Response(
                {'error': 'Usernames do not match.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_username == request.user.username:
            return Response(
                {'error': 'New username must be different from your current username.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(username=new_username).exists():
            # Match the requested format for duplicate username
            return Response(
                {'username': ['This username is already taken.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.username = new_username
        request.user.save(update_fields=['username'])

        return Response(
            {
                'message': 'Username updated successfully.',
                'username': new_username
            },
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


class ProfileImageView(APIView):
    """
    PUT    /api/profile/image/ — Update the authenticated user's profile image.
    DELETE /api/profile/image/ — Remove the authenticated user's profile image.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        if 'profileImage' not in request.FILES:
            return Response({'error': 'No image provided'}, status=status.HTTP_400_BAD_REQUEST)
            
        user = request.user
        user.profile_image = request.FILES['profileImage']
        user.save()
        return Response(UserSerializer(user, context={'request': request}).data)

    def delete(self, request):
        user = request.user
        if user.profile_image:
            user.profile_image.delete(save=False)
            user.profile_image = None
            user.save()
        return Response(UserSerializer(user, context={'request': request}).data)


class PublicProfileView(APIView):
    """
    GET /api/users/{id}/public-profile/
    Retrieve the public profile of any user.
    Only exposes non-sensitive data and calculated stats.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicProfileSerializer(user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


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
        queryset = Item.objects.filter(status='approved').select_related('user').prefetch_related('images')

        item_type = request.query_params.get('type', '').strip()
        search = request.query_params.get('search', '').strip()

        # Role-based visibility rules
        if request.user.role == 'owner':
            matched_found_q = get_matched_found_items_query_for_owner(request.user)
            if item_type == 'lost':
                queryset = queryset.filter(type='lost', user=request.user)
            elif item_type == 'found':
                queryset = queryset.filter(type='found').filter(matched_found_q)
            else:
                # All tab: Owner's own lost items + matched found items
                queryset = queryset.filter(
                    Q(type='lost', user=request.user) |
                    (Q(type='found') & matched_found_q)
                )
        elif request.user.role == 'finder':
            if item_type == 'found':
                queryset = queryset.filter(type='found', user=request.user)
            elif item_type == 'lost':
                queryset = queryset.filter(type='lost')
            else:
                queryset = queryset.filter(Q(type='lost') | Q(type='found', user=request.user))
        else:
            # Fallback for admins or other roles
            if item_type:
                queryset = queryset.filter(type=item_type)

        now = timezone.now()
        
        queryset = queryset.annotate(
            active_featured=Case(
                When(is_featured=True, featured_until__gt=now, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        
        if search:
            queryset = queryset.filter(
                Q(category__icontains=search)
                | Q(title__icontains=search)
                | Q(description__icontains=search)
            ).annotate(
                match_score=Case(
                    When(category__iexact=search, then=Value(4)),
                    When(category__icontains=search, then=Value(3)),
                    When(title__icontains=search, then=Value(2)),
                    When(description__icontains=search, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            ).order_by('-active_featured', '-match_score', '-reported_at')
        else:
            queryset = queryset.order_by('-active_featured', '-reported_at')

        # Category filter
        category = request.query_params.get('category', '').strip()
        if category:
            queryset = queryset.filter(category=category)

        serializer = ItemSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ItemSerializer(data=request.data, context={'request': request})
        
        # Pre-validate images
        images = request.FILES.getlist('images')
        if len(images) > 5:
            return Response({'error': 'You can only upload up to 5 images.'}, status=status.HTTP_400_BAD_REQUEST)
        
        for img in images:
            if img.size > 5 * 1024 * 1024:
                return Response({'error': 'Each image must be smaller than 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)
            ext = img.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                return Response({'error': 'Unsupported format. Allowed: JPG, JPEG, PNG, WEBP.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            item = serializer.save(user=request.user, status='pending')
            
            # Save images
            for img in images:
                ItemImage.objects.create(item=item, image=img)
                
            # Award points for reporting a found item
            if item.type == 'found':
                award_found_report_points(request.user, item)

            return Response(ItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)
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
            
        # Enforce role-based visibility rules for detail view
        if request.user.role == 'owner':
            if item.user != request.user:
                if item.type == 'found':
                    if not is_found_item_matched_for_owner(item, request.user):
                        return Response({'error': 'You do not have permission to view this item.'}, status=status.HTTP_403_FORBIDDEN)
                else:
                    return Response({'error': 'You do not have permission to view this item.'}, status=status.HTTP_403_FORBIDDEN)
        elif request.user.role == 'finder':
            if item.type == 'found' and item.user != request.user:
                has_conv = Conversation.objects.filter(item=item, finder=request.user).exists()
                if not has_conv:
                    return Response({'error': 'You do not have permission to view this found item.'}, status=status.HTTP_403_FORBIDDEN)

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
# Item Return Views
# ─────────────────────────────────────────────────────────────────────────────

class MarkItemReturnedView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        if item.user != request.user:
            return Response({'error': 'Only the owner can mark the item as returned'}, status=status.HTTP_403_FORBIDDEN)

        if item.status == 'resolved':
            return Response({'error': 'Item is already resolved'}, status=status.HTTP_400_BAD_REQUEST)

        item.owner_returned_confirm = True
        item.save(update_fields=['owner_returned_confirm', 'updated_at'])

        # Notify the finder via Conversation if one exists
        conversations = Conversation.objects.filter(item=item)
        if conversations.exists():
            for conv in conversations:
                other_user = conv.finder if conv.owner == request.user else conv.owner
                Notification.objects.create(
                    user=other_user,
                    type='message',
                    message=f'The user {request.user.username} has marked "{item.title}" as returned. Please confirm.',
                    related_item=item
                )

        return Response({'message': 'Return confirmation sent to finder'}, status=status.HTTP_200_OK)

class ConfirmItemReturnView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        if item.user == request.user:
            return Response({'error': 'The owner cannot confirm the return on behalf of the finder'}, status=status.HTTP_403_FORBIDDEN)

        if not item.owner_returned_confirm:
            return Response({'error': 'The owner has not marked this item as returned yet'}, status=status.HTTP_400_BAD_REQUEST)
        
        if item.status == 'resolved':
            return Response({'message': 'Item is already resolved'}, status=status.HTTP_200_OK)

        item.finder_returned_confirm = True
        item.status = 'resolved'
        item.resolved_at = timezone.now()
        item.save(update_fields=['finder_returned_confirm', 'status', 'resolved_at', 'updated_at'])

        # Determine finder and owner for reputation points and rating
        if item.type == 'lost':
            finder_user = request.user
            owner_user = item.user
        else:
            finder_user = item.user
            owner_user = request.user

        process_successful_return_reward(finder=finder_user, owner=owner_user, item=item)

        Notification.objects.create(
            user=item.user,
            type='message',
            message=f'{request.user.username} confirmed the return of "{item.title}". Item is now resolved.',
            related_item=item
        )

        return Response({'message': 'Item return confirmed and resolved'}, status=status.HTTP_200_OK)

class MyReportsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        queryset = Item.objects.filter(user=request.user).prefetch_related('images')

        filter_param = (request.query_params.get('filter') or request.query_params.get('type') or '').lower()
        status_param = (request.query_params.get('status') or '').lower()

        if filter_param == 'found':
            # All found items reported by this finder
            queryset = queryset.filter(type='found')
        elif filter_param in ['recovered', 'resolved', 'items_recovered', 'successful_returns', 'successful-returns']:
            # Successfully recovered found items by this finder
            queryset = queryset.filter(type='found', status='resolved')
        elif filter_param == 'lost':
            queryset = queryset.filter(type='lost')
        elif status_param == 'resolved':
            queryset = queryset.filter(type='found', status='resolved')
        elif status_param == 'active':
            queryset = queryset.filter(type='found').exclude(status='resolved')

        queryset = queryset.annotate(
            active_featured=Case(
                When(is_featured=True, featured_until__gt=now, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ).order_by('-active_featured', '-reported_at').distinct()
        serializer = ItemSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────────────────────────────────────
# Chat Views
# ─────────────────────────────────────────────────────────────────────────────

class ConversationListView(APIView):
    """
    GET /api/conversations/ — Retrieve all conversations for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(
            (Q(owner_id=request.user.id) & Q(hidden_by_owner=False)) | 
            (Q(finder_id=request.user.id) & Q(hidden_by_finder=False))
        ).annotate(
            last_msg_time=Max('messages__sent_at')
        ).select_related('item', 'owner', 'finder').prefetch_related('messages', 'messages__sender').order_by('-last_msg_time', '-created_at').distinct()

        serializer = ConversationSerializer(conversations, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ConversationInitView(APIView):
    """
    POST /api/conversations/init/ — Get or create a conversation for an item.
    Body: { "item_id": 123 }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        item_id = request.data.get('item_id')
        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(id=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if item.user == request.user:
            return Response({'error': 'Owner cannot initiate conversation with themselves'}, status=status.HTTP_400_BAD_REQUEST)
            
        # Always map owner and finder strictly based on item type
        if item.type == 'lost':
            # For lost items, the poster is the owner, replier is the finder
            owner_user = item.user
            finder_user = request.user
        else:
            # For found items, the poster is the finder, replier is the owner
            owner_user = request.user
            finder_user = item.user
            
        # Search for any existing conversation between these two users FOR THIS SPECIFIC ITEM
        # Check both orientations to ensure we never duplicate a conversation
        # if the IDs were somehow flipped.
        conversation = Conversation.objects.filter(
            Q(item=item) & (
                (Q(owner_id=owner_user.id) & Q(finder_id=finder_user.id)) |
                (Q(owner_id=finder_user.id) & Q(finder_id=owner_user.id))
            )
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create(
                item_id=item.id,
                owner_id=owner_user.id,
                finder_id=finder_user.id
            )
        
        return Response({'conversation_id': conversation.id}, status=status.HTTP_200_OK)


class ChatListView(APIView):
    """
    GET  /api/chat/?conversation_id={id} — Retrieve all messages for a conversation.
    POST /api/chat/                      — Send a message to a conversation.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response(
                {'error': 'conversation_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if request.user.id != conversation.owner_id and request.user.id != conversation.finder_id:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        messages = ChatMessage.objects.filter(conversation=conversation).select_related('sender')

        filtered_messages = []
        for msg in messages:
            is_deleted_for_me = (msg.deleted_by_sender and msg.sender == request.user) or (msg.deleted_by_receiver and msg.sender != request.user)
            if is_deleted_for_me:
                continue
            if msg.deleted_for_everyone:
                msg.message = "This message was deleted"
                msg.message_type = 'text'
                msg.caption = None
                if msg.image:
                    msg.image.name = None
                msg.deleted_for_everyone = True # Forces italic styling and removes click listener in frontend
            filtered_messages.append(msg)

        # Mark messages sent to this user as read
        messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

        serializer = ChatMessageSerializer(filtered_messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        conversation_id = request.data.get('conversation')
        if not conversation_id:
            return Response({'error': 'conversation is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if request.user.id != conversation.owner_id and request.user.id != conversation.finder_id:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)

        serializer = ChatMessageSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            message = serializer.save(sender=request.user, conversation=conversation)
            
            # Reset hidden flags if the conversation was removed but a new message arrives
            if conversation.hidden_by_owner or conversation.hidden_by_finder:
                conversation.hidden_by_owner = False
                conversation.hidden_by_finder = False
                conversation.save(update_fields=['hidden_by_owner', 'hidden_by_finder'])
            
            receiver = conversation.owner if request.user.id == conversation.finder_id else conversation.finder

            # Notify the receiver
            Notification.objects.create(
                user=receiver,
                type='message',
                message=(
                    f'New message from '
                    f'{request.user.get_full_name() or request.user.username}: '
                    f'{message.message[:60]}'
                ),
                related_item=conversation.item,
            )

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────────────────────────────────────
# Modern Chat Views
# ─────────────────────────────────────────────────────────────────────────────

class ChatProfileView(APIView):
    """
    GET /api/chat/profile/?conversation_id={id}
    Returns the profile details of the OTHER user in the conversation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response({'error': 'conversation_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            conversation = Conversation.objects.get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        if request.user != conversation.owner and request.user != conversation.finder:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        other_user = conversation.owner if request.user.id == conversation.finder_id else conversation.finder
        
        serializer = PublicProfileSerializer(other_user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatMessageDetailView(APIView):
    """
    PUT /api/chat/message/{id}/
    DELETE /api/chat/message/{id}/
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            message = ChatMessage.objects.get(pk=pk)
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if request.user.id not in [message.conversation.owner_id, message.conversation.finder_id]:
            return Response({'error': 'You can only edit messages in your conversations'}, status=status.HTTP_403_FORBIDDEN)
            
        if message.deleted_for_everyone:
            return Response({'error': 'Cannot edit a deleted message'}, status=status.HTTP_400_BAD_REQUEST)
            
        update_fields = ['is_edited', 'edited_at']

        if message.message_type == 'image':
            new_text = request.data.get('caption')
            if new_text is None:  # In case frontend sends 'message' key instead
                new_text = request.data.get('message')
            if new_text is not None:
                message.caption = new_text
                update_fields.append('caption')

            new_image = request.FILES.get('image')
            if new_image:
                message.image = new_image
                update_fields.append('image')
                
            if new_text is None and not new_image:
                return Response({'error': 'Caption text or image is required'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            new_text = request.data.get('message')
            if not new_text:
                return Response({'error': 'Message text is required'}, status=status.HTTP_400_BAD_REQUEST)
            message.message = new_text
            update_fields.append('message')
            
        message.is_edited = True
        message.edited_at = timezone.now()
        message.save(update_fields=update_fields)
        
        serializer = ChatMessageSerializer(message, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            message = ChatMessage.objects.get(pk=pk)
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)
            
        # Parse for_everyone boolean. It might come as a string 'true'/'false' or boolean
        for_everyone_val = request.data.get('for_everyone') or request.query_params.get('for_everyone', False)
        if isinstance(for_everyone_val, str):
            for_everyone = for_everyone_val.lower() == 'true'
        else:
            for_everyone = bool(for_everyone_val)
            
        if for_everyone:
            if message.sender != request.user:
                return Response({'error': 'You can only delete your own messages for everyone'}, status=status.HTTP_403_FORBIDDEN)
            message.deleted_for_everyone = True
            message.save(update_fields=['deleted_for_everyone'])
        else:
            # Delete for me
            if message.sender == request.user:
                message.deleted_by_sender = True
                message.save(update_fields=['deleted_by_sender'])
            else:
                # User is receiver
                message.deleted_by_receiver = True
                message.save(update_fields=['deleted_by_receiver'])
                
        return Response({'message': 'Message deleted successfully'}, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """
    DELETE /api/chat/conversation/{id}/
    Removes the conversation from the user's chat list.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
            
        if request.user.id != conversation.owner_id and request.user.id != conversation.finder_id:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
            
        if request.user.id == conversation.owner_id:
            conversation.hidden_by_owner = True
            conversation.save(update_fields=['hidden_by_owner'])
            ChatMessage.objects.filter(conversation=conversation, sender=request.user).update(deleted_by_sender=True)
            ChatMessage.objects.filter(conversation=conversation).exclude(sender=request.user).update(deleted_by_receiver=True)
        else:
            conversation.hidden_by_finder = True
            conversation.save(update_fields=['hidden_by_finder'])
            ChatMessage.objects.filter(conversation=conversation, sender=request.user).update(deleted_by_sender=True)
            ChatMessage.objects.filter(conversation=conversation).exclude(sender=request.user).update(deleted_by_receiver=True)
            
        return Response({'message': 'Conversation removed'}, status=status.HTTP_200_OK)


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


# ─────────────────────────────────────────────────────────────────────────────
# Reputation & Points Views
# ─────────────────────────────────────────────────────────────────────────────

class ReputationProfileView(APIView):
    """
    GET /api/reputation/me/
    Retrieve the authenticated user's reputation, points, and badge status.
    Available ONLY for Finders.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'finder':
            return Response(
                {'error': 'Reputation and points are only available for Finders.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        rep = get_or_create_reputation(request.user)
        serializer = FinderReputationSerializer(rep, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class PointHistoryView(APIView):
    """
    GET /api/reputation/history/
    Retrieve all point ledger transactions for the authenticated user.
    Available ONLY for Finders.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'finder':
            return Response(
                {'error': 'Point history is only available for Finders.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        transactions = (
            PointTransaction.objects.filter(user=request.user)
            .select_related('related_item')
            .order_by('-created_at')
        )
        serializer = PointTransactionSerializer(transactions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RateFinderView(APIView):
    """
    POST /api/reputation/rate/
    Submit a 1-5 star rating and optional review for a Finder after a successful return.
    Available ONLY for Owners rating Finders on resolved items.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.role != 'owner':
            return Response(
                {'error': 'Only Owners can rate Finders.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = RateFinderRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        item_id = serializer.validated_data['item_id']
        rating_value = serializer.validated_data['rating']
        review_text = serializer.validated_data.get('review', '')

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        try:
            rating_obj = submit_finder_rating(
                owner=request.user,
                item=item,
                rating_value=rating_value,
                review_text=review_text,
            )
            return Response(
                FinderRatingSerializer(rating_obj).data,
                status=status.HTTP_201_CREATED,
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RatingStatusView(APIView):
    """
    GET /api/reputation/rating-status/?item_id={id}
    Check if the current user can rate the finder on this item, or if already rated.
    Only Owners can rate Finders on resolved items.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if request.user.role != 'owner':
            return Response({
                'can_rate': False,
                'has_rated': False,
                'rating': None,
            }, status=status.HTTP_200_OK)

        item_id = request.query_params.get('item_id')
        if not item_id:
            return Response({'error': 'item_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = Item.objects.get(pk=item_id)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        is_resolved = item.status == 'resolved'
        is_owner = False
        finder_id = None

        if item.type == 'lost':
            is_owner = (item.user == request.user)
            return_tx = PointTransaction.objects.filter(
                related_item=item, transaction_type='SUCCESSFUL_RETURN'
            ).first()
            if return_tx:
                finder_id = return_tx.user_id
            else:
                conv = Conversation.objects.filter(item=item).first()
                if conv:
                    finder_id = conv.finder_id
        else:
            finder_id = item.user_id
            conv = Conversation.objects.filter(item=item).first()
            if conv and conv.owner_id == request.user.id:
                is_owner = True
            elif item.user != request.user:
                is_owner = True

        existing_rating = FinderRating.objects.filter(owner=request.user, item=item).first()
        can_rate = (
            is_resolved
            and is_owner
            and (existing_rating is None)
            and (finder_id is not None)
            and (finder_id != request.user.id)
        )

        return Response({
            'can_rate': bool(can_rate),
            'has_rated': existing_rating is not None,
            'rating': FinderRatingSerializer(existing_rating).data if existing_rating else None,
        }, status=status.HTTP_200_OK)

