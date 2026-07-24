"""
DRF Serializers for the Findora API.

Each serializer maps a model to its wire-format representation,
applies validation rules from the specification, and guards
read-only / write-only fields appropriately.
"""

import re

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import ChatMessage, Claim, Item, Notification, User


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


# ─── Item Serializer ──────────────────────────────────────────────────────────

class ItemSerializer(serializers.ModelSerializer):
    """
    Full item serializer.

    Adds computed fields for the reporter's display name and role
    so the Android app can show them without a separate profile request.
    """

    user_name = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = '__all__'
        read_only_fields = ['user', 'status', 'reported_at', 'updated_at']

    def get_user_name(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_role(self, obj):
        return obj.user.role

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

class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages, including computed sender info."""

    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessage
        fields = '__all__'
        read_only_fields = ['sender', 'is_read', 'sent_at']

    def get_sender_name(self, obj):
        return obj.sender.get_full_name() or obj.sender.username

    def get_sender_role(self, obj):
        return obj.sender.role


# ─── Notification Serializer ──────────────────────────────────────────────────

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for user notifications."""

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ['user', 'type', 'message', 'related_item', 'created_at']
