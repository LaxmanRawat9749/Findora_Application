"""
DRF Serializers for the Findora API.

Each serializer maps a model to its wire-format representation,
applies validation rules from the specification, and guards
read-only / write-only fields appropriately.
"""

import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import ChatMessage, Claim, Conversation, Item, ItemImage, Notification, User


# ─── User Serializers ─────────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Read-only serializer for displaying a user's public profile data."""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone', 'role', 'is_verified', 'profile_image',
            'emergency_contact_name', 'emergency_contact_phone',
            'created_at',
        ]
        read_only_fields = ['id', 'is_verified', 'created_at']


class PublicProfileSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for public profiles (e.g., accessed from chat).
    Never exposes email, password, phone, or OTP tokens.
    """
    lost_reports = serializers.SerializerMethodField()
    found_reports = serializers.SerializerMethodField()
    recovered_items = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'role', 
            'profile_image', 'created_at', 'lost_reports', 'found_reports', 'recovered_items'
        ]
        
    def get_profile_image(self, obj):
        request = self.context.get('request')
        if obj.profile_image and request:
            return request.build_absolute_uri(obj.profile_image.url)
        return None

    def get_lost_reports(self, obj):
        return Item.objects.filter(user=obj, type='lost').count()
        
    def get_found_reports(self, obj):
        return Item.objects.filter(user=obj, type='found').count()
        
    def get_recovered_items(self, obj):
        return Item.objects.filter(user=obj, status='resolved').count()


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
        if value == 'admin':
            raise serializers.ValidationError("Cannot register as admin.")
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

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


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
        read_only_fields = ['user', 'status', 'reported_at', 'updated_at']

    def validate(self, data):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user_role = getattr(request.user, 'role', None)
            item_type = data.get('type')
            
            if item_type:
                if user_role == 'owner' and item_type != 'lost':
                    raise serializers.ValidationError({"type": "Owners can only report lost items."})
                if user_role == 'finder' and item_type != 'found':
                    raise serializers.ValidationError({"type": "Finders can only report found items."})
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


# ─── Chat Serializer ──────────────────────────────────────────────────────────

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
        return messages[0].message

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
