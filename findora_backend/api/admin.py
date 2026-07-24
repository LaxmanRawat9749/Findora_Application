"""
Findora Django Admin Configuration.

Enhances the default Django admin panel with:
  - Custom list displays with colored status badges
  - Search and filter capabilities for all models
  - Bulk admin actions (approve, reject, verify, unlock)
  - Inline claim display on item detail pages
  - Image preview for item photos
  - Custom site branding
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import ChatMessage, Claim, Item, Notification, OTPToken, User


# ─── User Admin ───────────────────────────────────────────────────────────────

@admin.register(User)
class FindoraUserAdmin(UserAdmin):
    """
    Admin interface for Findora users.

    Extends Django's built-in UserAdmin to expose Findora-specific
    fields: role, verification status, account locking, and emergency contacts.
    """

    list_display = [
        'username', 'email', 'full_name', 'role',
        'is_verified', 'is_locked', 'failed_login_attempts',
        'is_active', 'created_at',
    ]
    list_filter = ['role', 'is_verified', 'is_locked', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'failed_login_attempts']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Account Info', {
            'fields': ('username', 'email', 'password'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'role', 'profile_image'),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',),
        }),
        ('Status & Security', {
            'fields': (
                'is_active', 'is_verified', 'is_locked', 'locked_until',
                'failed_login_attempts',
            ),
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['verify_users', 'unlock_users', 'deactivate_users', 'activate_users']

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Full Name')
    def full_name(self, obj):
        return obj.get_full_name() or '—'

    # ─── Bulk Actions ─────────────────────────────────────────────────────────

    @admin.action(description='Mark selected users as verified')
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} user(s) successfully verified.')

    @admin.action(description='Unlock selected accounts')
    def unlock_users(self, request, queryset):
        queryset.update(is_locked=False, failed_login_attempts=0, locked_until=None)
        self.message_user(request, 'Selected accounts have been unlocked.')

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')


# ─── Item Admin ───────────────────────────────────────────────────────────────

class ClaimInline(admin.TabularInline):
    """Inline claim display within the Item admin detail page."""

    model = Claim
    extra = 0
    readonly_fields = ['claimant', 'status', 'proof_description', 'claimed_at']
    can_delete = False
    show_change_link = True


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin interface for lost/found item reports.

    Features colored status and type badges, image preview,
    inline claim display, and bulk approve/reject/resolve actions.
    """

    list_display = [
        'title', 'type_badge', 'category', 'status_badge',
        'reporter', 'location', 'reward_display', 'reported_at',
    ]
    list_filter = ['type', 'status', 'category', 'reported_at']
    search_fields = ['title', 'description', 'location', 'user__username', 'user__email']
    ordering = ['-reported_at']
    readonly_fields = ['user', 'reported_at', 'updated_at', 'qr_code', 'image_preview']
    list_per_page = 20
    date_hierarchy = 'reported_at'
    inlines = [ClaimInline]

    fieldsets = (
        ('Item Info', {
            'fields': ('user', 'type', 'title', 'description', 'category'),
        }),
        ('Status & Reward', {
            'fields': ('status', 'reward'),
        }),
        ('Location', {
            'fields': ('location', 'latitude', 'longitude'),
        }),
        ('Media & QR', {
            'fields': ('image', 'image_preview', 'qr_code'),
        }),
        ('Timestamps', {
            'fields': ('reported_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_items', 'reject_items', 'mark_resolved']

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Type')
    def type_badge(self, obj):
        color = '#D85A30' if obj.type == 'lost' else '#1D9E75'
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, obj.type.upper(),
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#854F0B',
            'approved': '#1D9E75',
            'resolved': '#534AB7',
            'rejected': '#D85A30',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, obj.status.upper(),
        )

    @admin.display(description='Reported By')
    def reporter(self, obj):
        return f"{obj.user.get_full_name() or obj.user.username} ({obj.user.role})"

    @admin.display(description='Reward')
    def reward_display(self, obj):
        return f"Rs. {obj.reward}" if obj.reward > 0 else '—'

    @admin.display(description='Image Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:150px;border-radius:8px;'
                'box-shadow:0 2px 8px rgba(0,0,0,0.15)"/>',
                obj.image.url,
            )
        return '—'

    # ─── Bulk Actions ─────────────────────────────────────────────────────────

    @admin.action(description='Approve selected items')
    def approve_items(self, request, queryset):
        count = queryset.update(status='approved')
        self.message_user(request, f'{count} item(s) approved successfully.')

    @admin.action(description='Reject selected items')
    def reject_items(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} item(s) rejected.')

    @admin.action(description='Mark selected items as resolved')
    def mark_resolved(self, request, queryset):
        count = queryset.update(status='resolved')
        self.message_user(request, f'{count} item(s) marked as resolved.')


# ─── Claim Admin ──────────────────────────────────────────────────────────────

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    """Admin interface for ownership claims."""

    list_display = ['item', 'claimant', 'status', 'claimed_at']
    list_filter = ['status', 'claimed_at']
    search_fields = ['item__title', 'claimant__username', 'claimant__email']
    readonly_fields = ['item', 'claimant', 'claimed_at']
    ordering = ['-claimed_at']

    actions = ['approve_claims', 'reject_claims']

    @admin.action(description='Approve selected claims')
    def approve_claims(self, request, queryset):
        count = queryset.update(status='approved')
        self.message_user(request, f'{count} claim(s) approved.')

    @admin.action(description='Reject selected claims')
    def reject_claims(self, request, queryset):
        count = queryset.update(status='rejected')
        self.message_user(request, f'{count} claim(s) rejected.')


# ─── Chat Admin ───────────────────────────────────────────────────────────────

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for chat messages (read-only moderation view)."""

    list_display = ['sender', 'receiver', 'item', 'message_preview', 'is_read', 'sent_at']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['sender__username', 'receiver__username', 'message', 'item__title']
    readonly_fields = ['sender', 'receiver', 'item', 'message', 'sent_at']
    ordering = ['-sent_at']

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:60] + '…' if len(obj.message) > 60 else obj.message


# ─── Notification Admin ───────────────────────────────────────────────────────

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for system notifications."""

    list_display = ['user', 'type', 'message_preview', 'is_read', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']
    readonly_fields = ['user', 'type', 'message', 'related_item', 'created_at']
    ordering = ['-created_at']

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:80] + '…' if len(obj.message) > 80 else obj.message


# ─── OTP Token Admin ──────────────────────────────────────────────────────────

@admin.register(OTPToken)
class OTPTokenAdmin(admin.ModelAdmin):
    """Admin interface for OTP records (read-only for security)."""

    list_display = ['user', 'purpose', 'is_used', 'attempt_count', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['user', 'otp_code', 'purpose', 'is_used', 'attempt_count', 'expires_at', 'created_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        """OTPs should only be created programmatically, not via admin."""
        return False


# ─── Admin Site Branding ──────────────────────────────────────────────────────

admin.site.site_header = 'Findora Administration'
admin.site.site_title = 'Findora Admin'
admin.site.index_title = 'Lost & Found Management System'
