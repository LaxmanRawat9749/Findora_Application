"""
Findora database models.

Defines all entities for the Lost & Found Management System:
    - User           : Application users (Owner & Finder accounts)
    - Administrator  : Dedicated system administrator accounts
    - AdminAuditLog  : Audit trail for administrative actions
    - OTPToken       : Time-limited one-time passwords for verification / reset
    - Item           : Lost or found item reports
    - ItemImage      : Associated item photos
    - Claim          : Ownership claims submitted on found items
    - Conversation   : Direct chat threads between Owner and Finder
    - ChatMessage    : Individual messages in conversation threads
    - Notification   : System alerts delivered to individual users
    - Payment        : Featured listing promotions and gateway transactions
"""

import secrets
import string

from django.contrib.auth.models import AbstractBaseUser, AbstractUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# Application User Model (Owner & Finder ONLY)
# ─────────────────────────────────────────────────────────────────────────────

class User(AbstractUser):
    """
    Application user model representing Lost & Found participants (Owners and Finders).

    Administrators do NOT reside in this table — they are structurally isolated
    in the `Administrator` model to prevent operational hazards and data cross-talk.
    """

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('finder', 'Finder'),
    ]

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='owner')
    is_verified = models.BooleanField(default=False)
    failed_login_attempts = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    locked_until = models.DateTimeField(null=True, blank=True)
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_phone = models.CharField(max_length=15, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'Application User'
        verbose_name_plural = 'Application Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # ─── Account Lock Logic ───────────────────────────────────────────────────

    def is_account_locked(self):
        """Return True if the account is currently locked."""
        if self.is_locked and self.locked_until:
            if timezone.now() < self.locked_until:
                return True
            # Auto-unlock once the lock window has expired
            self.is_locked = False
            self.failed_login_attempts = 0
            self.locked_until = None
            self.save(update_fields=['is_locked', 'failed_login_attempts', 'locked_until'])
        return False

    def increment_failed_attempts(self):
        """Increment failed login counter; lock account after 5 attempts (30 min)."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            self.is_locked = True
            self.locked_until = timezone.now() + timezone.timedelta(minutes=30)
        self.save(update_fields=['failed_login_attempts', 'is_locked', 'locked_until'])

    def reset_failed_attempts(self):
        """Reset login counter and unlock account on successful authentication."""
        self.failed_login_attempts = 0
        self.is_locked = False
        self.locked_until = None
        self.save(update_fields=['failed_login_attempts', 'is_locked', 'locked_until'])


# ─────────────────────────────────────────────────────────────────────────────
# Dedicated Administrator Model
# ─────────────────────────────────────────────────────────────────────────────

class AdministratorManager(BaseUserManager):
    """Custom manager for Administrator accounts."""

    def create_admin(self, username, email, password=None, admin_role='super_admin', **extra_fields):
        if not username:
            raise ValueError('Administrator must have a username.')
        if not email:
            raise ValueError('Administrator must have an email address.')

        email = self.normalize_email(email)
        admin = self.model(
            username=username.strip(),
            email=email.strip().lower(),
            admin_role=admin_role,
            is_staff=True,
            is_active=True,
            **extra_fields,
        )
        if password:
            admin.set_password(password)
        else:
            admin.set_unusable_password()
        admin.save(using=self._db)
        return admin

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('admin_role', 'super_admin')
        return self.create_admin(username, email, password, **extra_fields)


class Administrator(AbstractBaseUser, PermissionsMixin):
    """
    Dedicated Administrator model for Django Admin and platform moderation.

    Completely isolated from the application `User` table.
    Admin accounts cannot be affected by user deletions, nor can they
    authenticate via the mobile Owner/Finder API.
    """

    ADMIN_ROLE_CHOICES = [
        ('super_admin', 'Super Administrator'),
        ('moderator', 'Moderator'),
        ('payment_manager', 'Payment Manager'),
        ('content_manager', 'Content Manager'),
    ]

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    admin_role = models.CharField(max_length=20, choices=ADMIN_ROLE_CHOICES, default='super_admin')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Custom related_names to avoid reverse-accessor conflicts with auth.User or api.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this administrator belongs to.',
        related_name='admin_groups',
        related_query_name='administrator',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this administrator.',
        related_name='admin_user_permissions',
        related_query_name='administrator',
    )

    objects = AdministratorManager()

    USERNAME_FIELD = 'username'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'administrators'
        verbose_name = 'Administrator'
        verbose_name_plural = 'Administrators'
        ordering = ['-created_at']

    def __str__(self):
        role_label = dict(self.ADMIN_ROLE_CHOICES).get(self.admin_role, self.admin_role)
        return f"{self.get_full_name() or self.username} ({role_label})"

    def get_full_name(self):
        full = f"{self.first_name} {self.last_name}".strip()
        return full or self.username

    def get_short_name(self):
        return self.first_name or self.username

    def has_perm(self, perm, obj=None):
        """Custom permission check based on admin role and permissions."""
        if not self.is_active:
            return False
        if self.is_superuser or self.admin_role == 'super_admin':
            return True

        # Role-based presets
        app_label = perm.split('.')[0] if '.' in perm else ''
        action = perm.split('.')[1] if '.' in perm else perm

        if self.admin_role == 'moderator':
            # Moderator can view/change users, items, claims, chats, notifications
            if app_label in ('api', 'auth'):
                if any(k in action for k in ['user', 'item', 'claim', 'conversation', 'chatmessage', 'notification']):
                    return True

        elif self.admin_role == 'payment_manager':
            # Payment manager handles payments and featured listings
            if any(k in action for k in ['payment', 'item']):
                return True

        elif self.admin_role == 'content_manager':
            # Content manager handles items, claims, item images
            if any(k in action for k in ['item', 'claim', 'itemimage']):
                return True

        return super().has_perm(perm, obj)

    def has_module_perms(self, app_label):
        """Module permission check."""
        if not self.is_active:
            return False
        if self.is_superuser or self.admin_role == 'super_admin':
            return True
        return True


# ─────────────────────────────────────────────────────────────────────────────
# Administrator Audit Log Model
# ─────────────────────────────────────────────────────────────────────────────

class AdminAuditLog(models.Model):
    """
    Audit log record capturing all administrative actions performed in Django Admin.
    """

    ACTION_CHOICES = [
        (1, 'Addition'),
        (2, 'Change'),
        (3, 'Deletion'),
        (4, 'Approval'),
        (5, 'Rejection'),
        (6, 'Resolution'),
        (7, 'Verification'),
        (8, 'Account Lock/Unlock'),
    ]

    admin = models.ForeignKey(
        Administrator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    admin_username = models.CharField(max_length=150, blank=True)
    action_time = models.DateTimeField(default=timezone.now)
    action_flag = models.PositiveSmallIntegerField(choices=ACTION_CHOICES, default=2)
    target_model = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    change_message = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        db_table = 'admin_audit_logs'
        ordering = ['-action_time']
        verbose_name = 'Admin Audit Log'
        verbose_name_plural = 'Admin Audit Logs'

    def __str__(self):
        action_name = dict(self.ACTION_CHOICES).get(self.action_flag, 'Action')
        return f"[{self.action_time.strftime('%Y-%m-%d %H:%M')}] {self.admin_username}: {action_name} on {self.object_repr}"


# ─────────────────────────────────────────────────────────────────────────────
# OTP & Verification
# ─────────────────────────────────────────────────────────────────────────────

class OTPToken(models.Model):
    """
    One-time password record used for email verification and password reset.
    """

    PURPOSE_CHOICES = [
        ('email_verify', 'Email Verification'),
        ('password_reset', 'Password Reset'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otp_tokens')
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    attempt_count = models.IntegerField(default=0)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'otp_tokens'
        verbose_name = 'OTP Token'
        verbose_name_plural = 'OTP Tokens'

    def __str__(self):
        return f"OTP for {self.user.email} ({self.purpose})"

    def is_valid(self):
        """Return True only if the OTP has not expired, not been used, and has attempts left."""
        return (
            not self.is_used
            and self.attempt_count < 5
            and timezone.now() < self.expires_at
        )

    def increment_attempt(self):
        """Record a failed verification attempt."""
        self.attempt_count += 1
        self.save(update_fields=['attempt_count'])

    @classmethod
    def generate_otp(cls):
        """Generate a cryptographically secure 6-digit numeric OTP."""
        return ''.join(secrets.choice(string.digits) for _ in range(6))


# ─────────────────────────────────────────────────────────────────────────────
# Item Management Models
# ─────────────────────────────────────────────────────────────────────────────

class Item(models.Model):
    """
    Represents a lost or found item report submitted by an Owner or Finder.
    """

    TYPE_CHOICES = [
        ('lost', 'Lost'),
        ('found', 'Found'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('resolved', 'Resolved'),
        ('rejected', 'Rejected'),
    ]
    CATEGORY_CHOICES = [
        ('wallet', 'Wallet'),
        ('phone', 'Phone'),
        ('keys', 'Keys'),
        ('bag', 'Bag'),
        ('id_card', 'ID Card'),
        ('documents', 'Documents'),
        ('electronics', 'Electronics'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    type = models.CharField(max_length=5, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    reward = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_featured = models.BooleanField(default=False)
    featured_until = models.DateTimeField(null=True, blank=True)
    owner_returned_confirm = models.BooleanField(default=False)
    finder_returned_confirm = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'items'
        ordering = ['-reported_at']
        verbose_name = 'Item'
        verbose_name_plural = 'Items'

    def __str__(self):
        return f"[{self.type.upper()}] {self.title} — {self.status}"


class ItemImage(models.Model):
    """
    Multiple photos associated with a reported item.
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'item_images'
        ordering = ['uploaded_at']
        verbose_name = 'Item Image'
        verbose_name_plural = 'Item Images'

    def __str__(self):
        return f"Image for {self.item.title}"


class Claim(models.Model):
    """
    Ownership claim submitted by a user on a found item.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='claims')
    claimant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    proof_description = models.TextField(blank=True)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'claims'
        verbose_name = 'Claim'
        verbose_name_plural = 'Claims'

    def __str__(self):
        return f"Claim by {self.claimant.username} on '{self.item.title}'"


# ─────────────────────────────────────────────────────────────────────────────
# Communication & Notifications
# ─────────────────────────────────────────────────────────────────────────────

class Conversation(models.Model):
    """
    Direct chat thread between an Owner and a Finder regarding a specific item.
    """
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='conversations')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owner_conversations')
    finder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='finder_conversations')
    hidden_by_owner = models.BooleanField(default=False)
    hidden_by_finder = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'conversations'
        unique_together = ('item', 'owner', 'finder')
        ordering = ['-created_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'

    def __str__(self):
        return f"Chat on {self.item.title} ({self.finder.username} & {self.owner.username})"


class ChatMessage(models.Model):
    """
    Direct message in a conversation.
    """

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', null=True)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField(blank=True)
    message_type = models.CharField(max_length=10, choices=[('text', 'Text'), ('image', 'Image')], default='text')
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    caption = models.TextField(blank=True)
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    deleted_for_everyone = models.BooleanField(default=False)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_receiver = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'chat_messages'
        ordering = ['sent_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'

    def __str__(self):
        preview = self.message[:40]
        return f"{self.sender.username}: {preview}"


class Notification(models.Model):
    """
    System notification delivered to an individual user.
    """

    TYPE_CHOICES = [
        ('match', 'Match Found'),
        ('approved', 'Report Approved'),
        ('rejected', 'Report Rejected'),
        ('message', 'New Message'),
        ('claim', 'Claim Update'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notifications',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        ordering = ['-created_at']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"[{self.type}] → {self.user.username}: {self.message[:50]}"


# ─────────────────────────────────────────────────────────────────────────────
# Payment & Featured Promotions
# ─────────────────────────────────────────────────────────────────────────────

class Payment(models.Model):
    """
    Payment transaction record for promoting items to featured listing status.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=10, default='NPR')
    provider = models.CharField(max_length=50, default='khalti')
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    promotion_duration = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment {self.id} for Item {self.item_id} - {self.status}"
