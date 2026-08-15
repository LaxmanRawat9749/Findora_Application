"""
Findora database models.

Defines all entities for the Lost & Found Management System:
    - User       : Extended AbstractUser with role, verification, and account-locking
    - OTPToken   : Time-limited one-time passwords for email verification / password reset
    - Item       : Lost or found item reports
    - Claim      : Ownership claims submitted on found items
    - ChatMessage: Direct messages between users about a specific item
    - Notification: System notifications delivered to individual users
"""

import secrets
import string

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """
    Custom user model that extends Django's AbstractUser.

    Adds Findora-specific fields: role, email verification status,
    account locking after repeated failed login attempts, and
    optional emergency contact / profile image.
    """

    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('finder', 'Finder'),
        ('admin', 'Admin'),
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
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"

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


class OTPToken(models.Model):
    """
    One-time password record used for email verification and password reset.

    Each OTP:
      - Is 6 digits long
      - Expires after 10 minutes
      - Allows a maximum of 5 verification attempts
      - Can only be used once (is_used flag)
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


class Item(models.Model):
    """
    Represents a lost or found item report submitted by a user.

    Status lifecycle: pending → approved → resolved (or rejected).
    Items are publicly visible only when status is 'approved'.
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
    Multiple images associated with a single reported item.
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
    Ownership claim submitted by a user (claimant) on a found item.

    Admin reviews the claim and either approves or rejects it.
    On approval, the related item status is updated to 'resolved'.
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


class Conversation(models.Model):
    """
    A conversation thread between an Owner and a Finder regarding a specific item.
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
    System notification delivered to a specific user.

    Types cover the full lifecycle: item matches, admin approvals/rejections,
    new chat messages, and claim status updates.
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


class Payment(models.Model):
    """
    Payment record for promoting an item to featured status.
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
