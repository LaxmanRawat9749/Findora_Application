"""
DRF Serializers for the Findora API.

Each serializer maps a model to its wire-format representation,
applies validation rules from the specification, and guards
read-only / write-only fields appropriately.
"""

import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import (
    ChatMessage,
    Claim,
    Conversation,
    FinderRating,
    FinderReputation,
    Item,
    ItemImage,
    Notification,
    PointTransaction,
    User,
    UserBadge,
)


# ─── User Serializers ─────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying a user's profile data."""
    total_points = serializers.SerializerMethodField()
    successful_returns = serializers.SerializerMethodField()
    successful_returns_count = serializers.SerializerMethodField()
    reputation_display = serializers.SerializerMethodField()
    is_trusted_finder = serializers.SerializerMethodField()
    primary_badge = serializers.SerializerMethodField()
    lost_reports = serializers.SerializerMethodField()
    lost_reports_count = serializers.SerializerMethodField()
    found_reports = serializers.SerializerMethodField()
    found_reports_count = serializers.SerializerMethodField()
    items_recovered = serializers.SerializerMethodField()
    recovered_items_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'is_verified', 'profile_image',
            'emergency_contact_name', 'emergency_contact_phone',
            'total_points', 'successful_returns', 'successful_returns_count',
            'reputation_display', 'is_trusted_finder',
            'primary_badge', 'lost_reports', 'lost_reports_count',
            'found_reports', 'found_reports_count',
            'items_recovered', 'recovered_items_count', 'created_at',
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']

    def get_is_trusted_finder(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return False
        rep = getattr(obj, 'reputation', None)
        return rep.is_trusted_finder if rep else False

    def get_total_points(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return 0
        rep = getattr(obj, 'reputation', None)
        return rep.total_points if rep else 0

    def get_successful_returns(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return 0
        return Item.objects.filter(user=obj, type='found', status='resolved').distinct().count()

    def get_successful_returns_count(self, obj):
        return self.get_successful_returns(obj)

    def get_reputation_display(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return "Not applicable"
        rep = getattr(obj, 'reputation', None)
        return rep.reputation_display if rep else "New Finder"

    def get_primary_badge(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return None
        rep = getattr(obj, 'reputation', None)
        return rep.primary_badge if rep else None

    def get_lost_reports(self, obj):
        return Item.objects.filter(user=obj, type='lost').distinct().count()

    def get_lost_reports_count(self, obj):
        return self.get_lost_reports(obj)

    def get_found_reports(self, obj):
        return Item.objects.filter(user=obj, type='found').distinct().count()

    def get_found_reports_count(self, obj):
        return self.get_found_reports(obj)

    def get_items_recovered(self, obj):
        return Item.objects.filter(user=obj, type='found', status='resolved').distinct().count()

    def get_recovered_items_count(self, obj):
        return self.get_items_recovered(obj)


class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for public profiles (e.g., accessed from chat or item details).
    Never exposes email, password, phone, or OTP tokens.
    """
    lost_reports = serializers.SerializerMethodField()
    lost_reports_count = serializers.SerializerMethodField()
    found_reports = serializers.SerializerMethodField()
    found_reports_count = serializers.SerializerMethodField()
    recovered_items = serializers.SerializerMethodField()
    items_recovered = serializers.SerializerMethodField()
    recovered_items_count = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    total_points = serializers.SerializerMethodField()
    successful_returns = serializers.SerializerMethodField()
    successful_returns_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    rating_count = serializers.SerializerMethodField()
    reputation_display = serializers.SerializerMethodField()
    is_trusted_finder = serializers.SerializerMethodField()
    primary_badge = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'role', 
            'profile_image', 'created_at', 'lost_reports', 'lost_reports_count',
            'found_reports', 'found_reports_count',
            'recovered_items', 'items_recovered', 'recovered_items_count',
            'total_points', 'successful_returns', 'successful_returns_count',
            'average_rating', 'rating_count', 'reputation_display', 'is_trusted_finder',
            'primary_badge', 'badges'
        ]

    def get_is_trusted_finder(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return False
        rep = getattr(obj, 'reputation', None)
        return rep.is_trusted_finder if rep else False
        
    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

    def get_lost_reports(self, obj):
        return Item.objects.filter(user=obj, type='lost').distinct().count()

    def get_lost_reports_count(self, obj):
        return self.get_lost_reports(obj)
        
    def get_found_reports(self, obj):
        return Item.objects.filter(user=obj, type='found').distinct().count()

    def get_found_reports_count(self, obj):
        return self.get_found_reports(obj)
        
    def get_recovered_items(self, obj):
        return Item.objects.filter(user=obj, type='found', status='resolved').distinct().count()

    def get_items_recovered(self, obj):
        return self.get_recovered_items(obj)

    def get_recovered_items_count(self, obj):
        return self.get_recovered_items(obj)

    def get_total_points(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return 0
        rep = getattr(obj, 'reputation', None)
        return rep.total_points if rep else 0

    def get_successful_returns(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return 0
        return Item.objects.filter(user=obj, type='found', status='resolved').distinct().count()

    def get_successful_returns_count(self, obj):
        return self.get_successful_returns(obj)

    def get_average_rating(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return None
        rep = getattr(obj, 'reputation', None)
        return rep.average_rating if rep else 0.0

    def get_rating_count(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return None
        rep = getattr(obj, 'reputation', None)
        return rep.rating_count if rep else 0

    def get_reputation_display(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return None
        rep = getattr(obj, 'reputation', None)
        return rep.reputation_display if rep else "New Finder"

    def get_primary_badge(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return None
        rep = getattr(obj, 'reputation', None)
        return rep.primary_badge if rep else None

    def get_badges(self, obj):
        if getattr(obj, 'role', '') != 'finder':
            return []
        badges = obj.badges.all().order_by('required_returns')
        return [
            {
                'key': b.badge_key,
                'name': b.name,
                'icon': b.icon,
                'description': b.description,
                'required_returns': b.required_returns,
            }
            for b in badges
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for new user registration.

    Validates:
      - username: 3–30 chars, alphanumeric + underscore only, unique
      - email: valid format, unique
      - password: passes Django's AUTH_PASSWORD_VALIDATORS (min 8 chars, etc.)
      - confirm_password: must match password
      - phone: exactly 10 digits
      - role: must be 'owner' or 'finder' (admin cannot self-register)
    """

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'},
    )
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    role = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'confirm_password',
            'first_name', 'last_name', 'phone', 'role',
        ]

    def validate_email(self, value):
        if value:
            return value.lower().strip()
        return value

    def validate_username(self, value):
        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', value):
            raise serializers.ValidationError(
                "Username must be 3–30 characters and contain only letters, digits, and underscores."
            )
        return value

    def validate_phone(self, value):
        if value and (not value.isdigit() or len(value) != 10):
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value

    def validate_role(self, value):
        if value:
            value = value.lower().strip()
        if value == 'admin':
            raise serializers.ValidationError("Cannot register as admin.")
        if value not in ['owner', 'finder']:
            raise serializers.ValidationError("Role must be 'owner' or 'finder'.")
        return value

    def validate(self, data):
        errors = {}

        confirm_password = data.pop('confirm_password', None)
        if data.get('password') != confirm_password:
            errors['confirm_password'] = ['Passwords do not match.']

        username = data.get('username')
        email = data.get('email')

        username_exists = False
        email_exists = False

        if username:
            username_exists = User.objects.filter(username__iexact=username).exists()

        if email:
            email_exists = User.objects.filter(email__iexact=email.lower().strip()).exists()

        if username_exists and email_exists:
            errors['username'] = ['Username already exists.']
            errors['email'] = ['Email already exists.']
        elif username_exists:
            errors['username'] = ['Username already exists.']
        elif email_exists:
            errors['email'] = ['Email already exists.']

        role = data.get('role')
        if not role:
            errors['role'] = ["Role is required ('owner' or 'finder')."]
        elif role == 'admin':
            errors['role'] = ["Cannot register as admin."]
        elif role not in ['owner', 'finder']:
            errors['role'] = ["Role must be 'owner' or 'finder'."]

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=validated_data.get('role', 'owner'),
            is_verified=False,
        )
        return user


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a user's own profile (non-sensitive fields only)."""

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone',
            'emergency_contact_name', 'emergency_contact_phone',
            'profile_image',
        ]


# ─── Item Serializers ─────────────────────────────────────────────────────────

class ItemImageSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ItemImage
        fields = ['id', 'image_url', 'uploaded_at']

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


class ItemSerializer(serializers.ModelSerializer):
    """
    Full item serializer.

    Adds computed fields for the reporter's display name and role
    so the Android app can show them without a separate profile request.
    """

    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    user_profile_image = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    images = ItemImageSerializer(many=True, read_only=True)

    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['user', 'status', 'reported_at', 'updated_at', 'is_featured', 'featured_until']

    def validate(self, data):
        request = self.context.get('request')
        user = getattr(request, 'user', None) if request else None
        if not user and request:
            user = getattr(request, '_force_auth_user', None)

        user_role = getattr(user, 'role', None) if user else None
        item_type = data.get('type', getattr(self.instance, 'type', None))

        if item_type and user_role:
            if user_role == 'owner' and item_type != 'lost':
                raise serializers.ValidationError({"type": "Owners can only report lost items."})
            if user_role == 'finder' and item_type != 'found':
                raise serializers.ValidationError({"type": "Finders can only report found items."})

        # Validate reward: Finder reports and found items must not have a reward amount
        reward = data.get('reward')
        if reward is not None:
            try:
                reward_num = float(reward)
            except (ValueError, TypeError):
                reward_num = 0.0
            if (user_role == 'finder' or item_type == 'found') and reward_num > 0:
                raise serializers.ValidationError({"reward": "Finder reports and found items cannot have a reward amount."})
            if user_role == 'finder' or item_type == 'found':
                data['reward'] = 0.00
        elif user_role == 'finder' or item_type == 'found':
            data['reward'] = 0.00

        return super().validate(data)

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_role(self, obj):
        return obj.user.role

    def get_user_profile_image(self, obj):
        request = self.context.get('request')
        if obj.user.profile_image and request:
            return request.build_absolute_uri(obj.user.profile_image.url)
        return None

    def get_image_url(self, obj):
        """Return absolute URL for the item image, or None."""
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ─── Claim Serializer ─────────────────────────────────────────────────────────

class ClaimSerializer(serializers.ModelSerializer):
    """Serializer for ownership claim submission and display."""

    claimant_name = serializers.SerializerMethodField()

    class Meta:
        model = Claim
        fields = '__all__'
        read_only_fields = ['claimant', 'status', 'claimed_at']

    def get_claimant_name(self, obj):
        return obj.claimant.get_full_name() or obj.claimant.username


# ─── Chat Serializers ─────────────────────────────────────────────────────────

class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation list items."""
    other_user_id = serializers.SerializerMethodField()
    other_user_name = serializers.SerializerMethodField()
    other_user_role = serializers.SerializerMethodField()
    item_title = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    last_message_time = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    other_user_profile_image = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id', 'item_title', 'item_type', 'other_user_id', 'other_user_name', 
            'other_user_role', 'other_user_profile_image', 'last_message', 'last_message_time', 'unread_count', 'created_at'
        ]

    def get_other_user(self, obj):
        request = self.context.get('request')
        if not request:
            return obj.finder
        return obj.finder if request.user.id == obj.owner_id else obj.owner

    def get_other_user_id(self, obj):
        return self.get_other_user(obj).id

    def get_other_user_name(self, obj):
        user = self.get_other_user(obj)
        return user.get_full_name() or user.username

    def get_other_user_role(self, obj):
        return self.get_other_user(obj).role

    def get_other_user_profile_image(self, obj):
        user = self.get_other_user(obj)
        request = self.context.get('request')
        if user.profile_image and request:
            return request.build_absolute_uri(user.profile_image.url)
        return None

    def get_item_title(self, obj):
        return obj.item.title

    def get_item_type(self, obj):
        return obj.item.type

    def get_last_message(self, obj):
        messages = list(obj.messages.all())
        if not messages:
            return ""
        messages.sort(key=lambda m: m.sent_at, reverse=True)
        last_msg = messages[0]
        request = self.context.get('request')
        is_deleted_for_me = False
        if request:
            is_deleted_for_me = (last_msg.deleted_by_sender and last_msg.sender == request.user) or (last_msg.deleted_by_receiver and last_msg.sender != request.user)
            
        if last_msg.deleted_for_everyone or is_deleted_for_me:
            return "This message was deleted"
        return last_msg.message

    def get_last_message_time(self, obj):
        messages = list(obj.messages.all())
        if not messages:
            return obj.created_at
        messages.sort(key=lambda m: m.sent_at, reverse=True)
        return messages[0].sent_at

    def get_unread_count(self, obj):
        request = self.context.get('request')
        if not request:
            return 0
        messages = list(obj.messages.all())
        return sum(1 for m in messages if m.sender_id != request.user.id and not m.is_read)


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages, including computed sender info."""

    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    sender_profile_image = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    message = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['sender', 'is_read', 'sent_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

    def get_sender_role(self, obj):
        return obj.sender.role

    def get_sender_profile_image(self, obj):
        request = self.context.get('request')
        if obj.sender.profile_image and request:
            return request.build_absolute_uri(obj.sender.profile_image.url)
        return None

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None


# ─── Notification Serializer ──────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications."""

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'type', 'message', 'related_item', 'created_at']


# ─── Reputation & Points Serializers ──────────────────────────────────────────

class UserBadgeSerializer(serializers.ModelSerializer):
    """Serializer for earned user achievements/badges."""

    class Meta:
        model = UserBadge
        fields = ['id', 'badge_key', 'name', 'description', 'required_returns', 'icon', 'earned_at']


class PointTransactionSerializer(serializers.ModelSerializer):
    """Serializer for point history transactions."""
    related_item_title = serializers.SerializerMethodField()

    class Meta:
        model = PointTransaction
        fields = [
            'id', 'points', 'transaction_type', 'description',
            'related_item', 'related_item_title', 'created_at',
        ]

    def get_related_item_title(self, obj):
        return obj.related_item.title if obj.related_item else None


class FinderRatingSerializer(serializers.ModelSerializer):
    """Serializer for owner ratings and reviews on finders."""
    owner_name = serializers.SerializerMethodField()
    finder_name = serializers.SerializerMethodField()
    item_title = serializers.SerializerMethodField()

    class Meta:
        model = FinderRating
        fields = [
            'id', 'owner', 'owner_name', 'finder', 'finder_name',
            'item', 'item_title', 'rating', 'review', 'created_at',
        ]
        read_only_fields = ['owner', 'finder', 'created_at']

    def get_owner_name(self, obj):
        return obj.owner.get_full_name() or obj.owner.username

    def get_finder_name(self, obj):
        return obj.finder.get_full_name() or obj.finder.username

    def get_item_title(self, obj):
        return obj.item.title if obj.item else None


class RateFinderRequestSerializer(serializers.Serializer):
    """Input serializer for rating a finder."""
    item_id = serializers.IntegerField(required=True)
    rating = serializers.IntegerField(min_value=1, max_value=5, required=True)
    review = serializers.CharField(required=False, allow_blank=True, default='')


class FinderReputationSerializer(serializers.ModelSerializer):
    """Comprehensive serializer for a finder's reputation profile."""
    reputation_display = serializers.CharField(read_only=True)
    primary_badge = serializers.CharField(read_only=True)
    is_trusted_finder = serializers.SerializerMethodField()
    successful_returns = serializers.SerializerMethodField()
    successful_returns_count = serializers.SerializerMethodField()
    lost_reports = serializers.SerializerMethodField()
    lost_reports_count = serializers.SerializerMethodField()
    found_reports = serializers.SerializerMethodField()
    found_reports_count = serializers.SerializerMethodField()
    items_recovered = serializers.SerializerMethodField()
    recovered_items_count = serializers.SerializerMethodField()
    badges = serializers.SerializerMethodField()
    badge_progress = serializers.SerializerMethodField()

    class Meta:
        model = FinderReputation
        fields = [
            'total_points', 'successful_returns', 'successful_returns_count',
            'rating_count', 'rating_sum',
            'average_rating', 'reputation_display', 'is_trusted_finder', 'primary_badge',
            'lost_reports', 'lost_reports_count',
            'found_reports', 'found_reports_count',
            'items_recovered', 'recovered_items_count',
            'badges', 'badge_progress', 'updated_at',
        ]

    def get_is_trusted_finder(self, obj):
        return obj.is_trusted_finder

    def get_successful_returns(self, obj):
        return obj.successful_returns

    def get_successful_returns_count(self, obj):
        return self.get_successful_returns(obj)

    def get_lost_reports(self, obj):
        return Item.objects.filter(user=obj.user, type='lost').distinct().count()

    def get_lost_reports_count(self, obj):
        return self.get_lost_reports(obj)

    def get_found_reports(self, obj):
        return Item.objects.filter(user=obj.user, type='found').distinct().count()

    def get_found_reports_count(self, obj):
        return self.get_found_reports(obj)

    def get_items_recovered(self, obj):
        return Item.objects.filter(user=obj.user, type='found', status='resolved').distinct().count()

    def get_recovered_items_count(self, obj):
        return self.get_items_recovered(obj)

    def get_badges(self, obj):
        badges = obj.user.badges.all().order_by('required_returns')
        return [
            {
                'key': b.badge_key,
                'name': b.name,
                'icon': b.icon,
                'description': b.description,
                'required_returns': b.required_returns,
            }
            for b in badges
        ]

    def get_badge_progress(self, obj):
        from .reputation_service import get_badge_progress_list
        return get_badge_progress_list(obj.user)

