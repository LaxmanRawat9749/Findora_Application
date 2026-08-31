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
  Reputation      : profile, points history, rating
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
    Claim,
    Conversation,
    FinderRating,
    FinderReputation,
    Item,
    ItemImage,
    Notification,
    OTPToken,
    Payment,
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
    get_or_create_matched_conversation,
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
            {'success': True, 'message': message},
            status=status.HTTP_200_OK,
        )


class ResendOTPView(APIView):
    """
    POST /api/resend-otp/
    Generate and dispatch a new OTP to the specified email address.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        purpose = request.data.get('purpose', 'email_verify')

        if not email:
            return Response(
                {'error': 'Email is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Invalidate existing unused tokens for this purpose
        OTPToken.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

        otp = create_otp(user, purpose)
        send_otp_email(user, otp.otp_code, purpose)

        return Response(
            {'message': 'OTP resent successfully.'},
            status=status.HTTP_200_OK,
        )


class LoginView(APIView):
    """
    POST /api/login/
    Authenticate a user and return JWT access + refresh tokens.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        start_ns = time.perf_counter_ns()
        username = request.data.get('username', '').strip()

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
                'user': UserSerializer(auth_user, context={'request': request}).data,
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
    Blacklist the supplied refresh token.
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
                {'error': 'Invalid or expired token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ForgotPasswordView(APIView):
    """
    POST /api/forgot-password/
    Send a password-reset OTP to the user's registered email address.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User with this email does not exist.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        OTPToken.objects.filter(user=user, purpose='password_reset', is_used=False).update(is_used=True)
        otp = create_otp(user, 'password_reset')
        send_otp_email(user, otp.otp_code, 'password_reset')

        return Response(
            {'message': 'Password reset OTP sent to your email.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    POST /api/reset-password/
    Verify OTP and set a new password for the specified user.
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        otp_code = request.data.get('otp', '').strip()
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if new_password != confirm_password:
            return Response(
                {'error': 'Passwords do not match.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        success, message = verify_otp(user, otp_code, 'password_reset')
        if not success:
            return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user=user)
        except Exception as e:
            return Response({'error': list(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.reset_failed_attempts()
        user.save()

        return Response(
            {'message': 'Password reset successfully. You may now log in.'},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """
    POST /api/change-password/
    Change password for the currently authenticated user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        old_password = request.data.get('old_password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if not request.user.check_password(old_password):
            return Response(
                {'old_password': ['Current password is incorrect.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_password != confirm_password:
            return Response(
                {'confirm_password': ['New passwords do not match.']},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user=request.user)
        except Exception as e:
            return Response(
                {'new_password': list(e.messages)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request.user.set_password(new_password)
        request.user.save()

        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK,
        )


class ChangeUsernameView(APIView):
    """
    POST /api/change-username/
    Allows the authenticated user to change their username.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        new_username = request.data.get('username', '').strip()
        current_password = request.data.get('password', '')

        if not new_username:
            return Response(
                {'username': ['New username is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', new_username):
            return Response(
                {'username': ['Username must be 3–30 characters and contain only letters, digits, and underscores.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not current_password:
            return Response(
                {'password': ['Current password is required to change username.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not request.user.check_password(current_password):
            return Response(
                {'password': ['Current password is incorrect.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if new_username.lower() == request.user.username.lower():
            return Response(
                {'username': ['New username cannot be the same as your current username.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        if User.objects.filter(username__iexact=new_username).exists():
            return Response(
                {'username': ['Username already exists.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.username = new_username
        request.user.save(update_fields=['username'])

        refresh = RefreshToken.for_user(request.user)

        return Response(
            {
                'message': 'Username changed successfully.',
                'user': UserSerializer(request.user, context={'request': request}).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────────────────────────────────────
# Profile Views
# ─────────────────────────────────────────────────────────────────────────────

class ProfileView(APIView):
    """
    GET  /api/profile/  — Retrieve the authenticated user's profile.
    PUT  /api/profile/  — Update non-sensitive profile fields.
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
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                UserSerializer(request.user, context={'request': request}).data,
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileImageView(APIView):
    """
    PUT    /api/profile/image/ — Upload/replace profile image.
    DELETE /api/profile/image/ — Remove profile image.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def post(self, request):
        return self.put(request)

    def patch(self, request):
        return self.put(request)

    def put(self, request):
        image = (
            request.FILES.get('image')
            or request.FILES.get('profileImage')
            or request.FILES.get('profile_image')
            or request.FILES.get('profile_picture')
        )
        if not image:
            return Response({'error': 'Image file is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file size (max 5 MB)
        if image.size > 5 * 1024 * 1024:
            return Response({'error': 'Image file must be smaller than 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file extension
        ext = image.name.split('.')[-1].lower() if '.' in image.name else ''
        if ext not in ['jpg', 'jpeg', 'png', 'webp']:
            return Response({'error': 'Unsupported format. Allowed: JPG, JPEG, PNG, WEBP.'}, status=status.HTTP_400_BAD_REQUEST)

        # Remove old image file if replacing
        if request.user.profile_image:
            try:
                request.user.profile_image.delete(save=False)
            except Exception:
                pass

        request.user.profile_image = image
        request.user.save(update_fields=['profile_image'])
        return Response(UserSerializer(request.user, context={'request': request}).data, status=status.HTTP_200_OK)

    def delete(self, request):
        if request.user.profile_image:
            try:
                request.user.profile_image.delete(save=False)
            except Exception:
                pass
            request.user.profile_image = None
            request.user.save(update_fields=['profile_image'])
        return Response({'message': 'Profile image removed successfully.'}, status=status.HTTP_200_OK)


class PublicProfileView(APIView):
    """
    GET /api/profile/{id}/ — Publicly view any user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        try:
            target_user = User.objects.select_related('reputation').prefetch_related('badges').get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PublicProfileSerializer(target_user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Item Views (Owner/Finder Role Model)
# ─────────────────────────────────────────────────────────────────────────────

class ItemListCreateView(APIView):
    """
    GET  /api/items/ — List approved items according to Findora visibility rules.
    POST /api/items/ — Report a new lost or found item.
    """

    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request):
        queryset = Item.objects.select_related('user').prefetch_related('images')

        item_type = request.query_params.get('type', '').strip()
        search = request.query_params.get('search', '').strip()

        # Role-based visibility rules
        if request.user.role == 'owner':
            matched_found_q = get_matched_found_items_query_for_owner(request.user)
            owner_own_lost = Q(user=request.user, type='lost', status='approved')
            matched_found = Q(type='found', status='approved') & matched_found_q
            if item_type == 'lost':
                queryset = queryset.filter(owner_own_lost)
            elif item_type == 'found':
                queryset = queryset.filter(matched_found)
            else:
                # All tab: Owner's own lost items + matched found items reported by Finders
                queryset = queryset.filter(owner_own_lost | matched_found)
        elif request.user.role == 'finder':
            approved_found = Q(type='found', status='approved')
            approved_lost = Q(type='lost', status='approved')
            if item_type == 'found':
                queryset = queryset.filter(approved_found)
            elif item_type == 'lost':
                queryset = queryset.filter(approved_lost)
            else:
                queryset = queryset.filter(approved_found | approved_lost)
        else:
            # Fallback for admins
            if item_type:
                queryset = queryset.filter(type=item_type)
            else:
                queryset = queryset.filter(status='approved')

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

        queryset = queryset.distinct()

        serializer = ItemSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ItemSerializer(data=request.data, context={'request': request})
        
        # Pre-validate images
        images = request.FILES.getlist('images')
        single_img = request.FILES.get('image')
        if single_img and single_img not in images:
            images.append(single_img)

        item_type = request.data.get('type')
        if not item_type and hasattr(request.user, 'role'):
            item_type = 'lost' if request.user.role == 'owner' else 'found'

        if item_type == 'lost' and len(images) > 1:
            return Response({'error': 'Only one photo can be uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        elif item_type == 'found':
            if len(images) == 0:
                return Response({'error': 'Please upload 1 photo of the found item.'}, status=status.HTTP_400_BAD_REQUEST)
            elif len(images) > 1:
                return Response({'error': 'Only one photo can be uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        elif len(images) > 1:
            return Response({'error': 'Only one photo can be uploaded.'}, status=status.HTTP_400_BAD_REQUEST)
        
        for img in images:
            if img.size > 5 * 1024 * 1024:
                return Response({'error': 'Each image must be smaller than 5 MB.'}, status=status.HTTP_400_BAD_REQUEST)
            ext = img.name.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                return Response({'error': 'Unsupported format. Allowed: JPG, JPEG, PNG, WEBP.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if serializer.is_valid():
            item = serializer.save(user=request.user, status='pending')
            
            # Save images
            for i, img in enumerate(images):
                if i == 0 and not item.image:
                    item.image = img
                    item.save(update_fields=['image'])
                if hasattr(img, 'seek'):
                    img.seek(0)
                ItemImage.objects.create(item=item, image=img)
                
            # Award points for reporting a found item
            if item.type == 'found':
                award_found_report_points(request.user, item)

            return Response(ItemSerializer(item, context={'request': request}).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ItemDetailView(APIView):
    """
    GET    /api/items/{id}/ — Retrieve a single item.
    PUT    /api/items/{id}/ — Update an item (creator only).
    DELETE /api/items/{id}/ — Delete an item (creator only).
    """

    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def _get_item(self, pk):
        try:
            return Item.objects.select_related('user', 'user__reputation').prefetch_related('images').get(pk=pk)
        except Item.DoesNotExist:
            return None

    def get(self, request, pk):
        item = self._get_item(pk)
        if not item:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Enforce visibility rules for detail view
        if request.user.role != 'admin':
            if item.user != request.user:
                if item.type == 'lost':
                    if item.status != 'approved':
                        return Response({'error': 'You do not have permission to view this item.'}, status=status.HTTP_403_FORBIDDEN)
                elif item.type == 'found':
                    if item.status != 'approved':
                        return Response({'error': 'You do not have permission to view this item.'}, status=status.HTTP_403_FORBIDDEN)
                    if request.user.role == 'owner':
                        is_matched = is_found_item_matched_for_owner(item, request.user)
                        has_conv = Conversation.objects.filter(
                            Q(item=item) & (Q(owner=request.user) | Q(finder=request.user))
                        ).exists()
                        has_claim = Claim.objects.filter(item=item, claimant=request.user).exists()
                        if not (is_matched or has_conv or has_claim):
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
    GET /api/admin/items/ — List items awaiting admin verification.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def get(self, request):
        status_filter = request.query_params.get('status', 'pending')
        items = Item.objects.filter(status=status_filter).select_related('user').order_by('-reported_at')
        serializer = ItemSerializer(items, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminVerifyItemView(APIView):
    """
    POST /api/admin/items/{id}/verify/ — Approve or reject an item report.
    """
    permission_classes = [permissions.IsAuthenticated, IsAdminRole]

    def post(self, request, pk):
        action = request.data.get('action', '').lower()
        if action not in ['approve', 'reject']:
            return Response(
                {'error': "Action must be 'approve' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            item = Item.objects.get(pk=pk)
        except Item.DoesNotExist:
            return Response({'error': 'Item not found.'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'approve':
            item.status = 'approved'
            item.save(update_fields=['status', 'updated_at'])
            Notification.objects.create(
                user=item.user,
                type='approved',
                message=f'Your report for "{item.title}" has been approved and is now public.',
                related_item=item,
            )
        else:
            item.status = 'rejected'
            item.save(update_fields=['status', 'updated_at'])
            Notification.objects.create(
                user=item.user,
                type='rejected',
                message=f'Your report for "{item.title}" was rejected.',
                related_item=item,
            )

        return Response(
            {
                'message': f'Item {action}d successfully.',
                'item': ItemSerializer(item, context={'request': request}).data,
            },
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
            return Response({'error': 'Only the reporter/owner can mark the item as returned'}, status=status.HTTP_403_FORBIDDEN)

        if item.status == 'resolved':
            return Response({'error': 'Item is already resolved'}, status=status.HTTP_400_BAD_REQUEST)

        item.owner_returned_confirm = True
        item.save(update_fields=['owner_returned_confirm', 'updated_at'])

        # Notify the return partner via Conversation if one exists
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
            return Response({'error': 'The reporter cannot confirm the return on behalf of the return partner'}, status=status.HTTP_403_FORBIDDEN)

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
            queryset = queryset.filter(type='found')
        elif filter_param in ['recovered', 'resolved', 'items_recovered', 'successful_returns', 'successful-returns']:
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        # Conversations where current user is participant and has not hidden it
        conversations = Conversation.objects.filter(
            (Q(owner=request.user, hidden_by_owner=False) | Q(finder=request.user, hidden_by_finder=False))
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
        item_id = request.data.get('item_id') or request.data.get('item')
        if not item_id:
            return Response({'error': 'item_id is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            item = Item.objects.get(id=item_id)
        except (Item.DoesNotExist, ValueError):
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
            
        conversation, err = get_or_create_matched_conversation(item, request.user)
        if err:
            return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({'conversation_id': conversation.id}, status=status.HTTP_200_OK)


class ChatListView(APIView):
    """
    GET  /api/chat/?item_id={id} or ?conversation_id={id} — List messages in conversation.
    POST /api/chat/ — Send a message within a conversation.
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        conversation_id = request.query_params.get('conversation_id') or request.query_params.get('conversation')
        item_id = request.query_params.get('item_id') or request.query_params.get('item')

        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except (Conversation.DoesNotExist, ValueError):
                return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
        elif item_id:
            try:
                item = Item.objects.get(id=item_id)
            except (Item.DoesNotExist, ValueError):
                return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)
            
            conversation, _ = get_or_create_matched_conversation(item, request.user)
            if not conversation:
                return Response([], status=status.HTTP_200_OK)

        if not conversation:
            return Response({'error': 'conversation_id or item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Check participation
        if conversation.owner != request.user and conversation.finder != request.user:
            return Response({'error': 'You are not a participant in this conversation'}, status=status.HTTP_403_FORBIDDEN)

        # Mark unread messages from other user as read
        ChatMessage.objects.filter(
            conversation=conversation,
            is_read=False
        ).exclude(sender=request.user).update(is_read=True)

        messages = ChatMessage.objects.filter(
            conversation=conversation,
            deleted_for_everyone=False
        ).select_related('sender').order_by('sent_at')

        after_id = request.query_params.get('after_id') or request.query_params.get('since_id')
        if after_id:
            try:
                messages = messages.filter(id__gt=int(after_id))
            except (ValueError, TypeError):
                pass

        # Filter out deleted for me
        filtered_messages = []
        for msg in messages:
            if msg.sender == request.user and msg.deleted_by_sender:
                continue
            if msg.sender != request.user and msg.deleted_by_receiver:
                continue
            filtered_messages.append(msg)

        serializer = ChatMessageSerializer(filtered_messages, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        conversation_id = request.data.get('conversation_id') or request.data.get('conversation')
        item_id = request.data.get('item_id') or request.data.get('item')

        conversation = None
        if conversation_id:
            try:
                conversation = Conversation.objects.get(id=conversation_id)
            except (Conversation.DoesNotExist, ValueError):
                return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
        elif item_id:
            try:
                item = Item.objects.get(id=item_id)
            except (Item.DoesNotExist, ValueError):
                return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

            conversation, err = get_or_create_matched_conversation(item, request.user)
            if err:
                return Response({'error': err}, status=status.HTTP_400_BAD_REQUEST)

        if not conversation:
            return Response({'error': 'conversation_id or item_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        if conversation.owner != request.user and conversation.finder != request.user:
            return Response({'error': 'You are not a participant in this conversation'}, status=status.HTTP_403_FORBIDDEN)

        message_type = request.data.get('message_type', 'text')
        message_text = request.data.get('message', '').strip()
        image_file = request.FILES.get('image')

        if message_type == 'image' and not image_file:
            return Response({'error': 'Image file is required for image message'}, status=status.HTTP_400_BAD_REQUEST)
        if message_type == 'text' and not message_text:
            return Response({'error': 'Message text cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        chat_msg = ChatMessage.objects.create(
            conversation=conversation,
            sender=request.user,
            message=message_text,
            message_type=message_type,
            image=image_file,
            caption=request.data.get('caption', '').strip()
        )

        # Unhide conversation for both parties when a new message is sent
        conversation.hidden_by_owner = False
        conversation.hidden_by_finder = False
        conversation.save(update_fields=['hidden_by_owner', 'hidden_by_finder'])

        # Notify the recipient
        recipient = conversation.finder if conversation.owner == request.user else conversation.owner
        Notification.objects.create(
            user=recipient,
            type='message',
            message=f'New message from {request.user.username}: {message_text[:40]}',
            related_item=conversation.item
        )

        serializer = ChatMessageSerializer(chat_msg, context={'request': request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ChatProfileView(APIView):
    """
    GET /api/chat/profile/?conversation_id={id}
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response({'error': 'conversation_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            conversation = Conversation.objects.select_related('item', 'owner', 'finder').get(id=conversation_id)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        if conversation.owner != request.user and conversation.finder != request.user:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        other_user = conversation.finder if conversation.owner == request.user else conversation.owner
        serializer = PublicProfileSerializer(other_user, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class ChatMessageDetailView(APIView):
    """
    PUT    /api/chat/messages/{id}/ — Edit a message
    DELETE /api/chat/messages/{id}/ — Delete for me or for everyone
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, pk):
        try:
            msg = ChatMessage.objects.select_related('conversation').get(pk=pk)
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

        if msg.sender != request.user:
            return Response({'error': 'Only sender can edit message'}, status=status.HTTP_403_FORBIDDEN)

        if msg.deleted_for_everyone:
            return Response({'error': 'Cannot edit deleted message'}, status=status.HTTP_400_BAD_REQUEST)

        new_text = request.data.get('message', '').strip()
        if not new_text:
            return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

        msg.message = new_text
        msg.is_edited = True
        msg.edited_at = timezone.now()
        msg.save(update_fields=['message', 'is_edited', 'edited_at'])

        return Response(ChatMessageSerializer(msg, context={'request': request}).data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            msg = ChatMessage.objects.select_related('conversation').get(pk=pk)
        except ChatMessage.DoesNotExist:
            return Response({'error': 'Message not found'}, status=status.HTTP_404_NOT_FOUND)

        delete_type = request.query_params.get('type', 'for_me')

        if delete_type == 'for_everyone':
            if msg.sender != request.user:
                return Response({'error': 'Only sender can delete for everyone'}, status=status.HTTP_403_FORBIDDEN)
            msg.deleted_for_everyone = True
            msg.save(update_fields=['deleted_for_everyone'])
        else:
            # Delete for me
            if msg.sender == request.user:
                msg.deleted_by_sender = True
                msg.save(update_fields=['deleted_by_sender'])
            else:
                msg.deleted_by_receiver = True
                msg.save(update_fields=['deleted_by_receiver'])

        return Response({'message': 'Message deleted successfully'}, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """
    DELETE /api/conversations/{id}/ — Clear / hide conversation for the user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            conversation = Conversation.objects.get(pk=pk)
        except Conversation.DoesNotExist:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)

        if conversation.owner == request.user:
            conversation.hidden_by_owner = True
            conversation.save(update_fields=['hidden_by_owner'])
        elif conversation.finder == request.user:
            conversation.hidden_by_finder = True
            conversation.save(update_fields=['hidden_by_finder'])
        else:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        return Response({'message': 'Conversation cleared successfully'}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────────────────────────────────────
# Notification Views
# ─────────────────────────────────────────────────────────────────────────────

class NotificationListView(APIView):
    """
    GET /api/notifications/ — List all notifications for the authenticated user.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        notifications = Notification.objects.filter(user=request.user).select_related('related_item').order_by('-created_at')
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MarkNotificationReadView(APIView):
    """
    POST /api/notifications/{id}/read/ — Mark a single notification as read.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        notif.is_read = True
        notif.save(update_fields=['is_read'])
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
