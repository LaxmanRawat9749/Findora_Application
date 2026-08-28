"""
Findora Django Admin Configuration.

Enhances the default Django admin panel with:
  - Unified User list display (Normal Users & Admins) showing activity, points & reputation
  - Item list display showing contextual reporter roles (Owner / Finder)
  - Search and filter capabilities for all models
  - Bulk admin actions (approve, reject, verify, unlock)
  - Inline claim display on item detail pages
  - Image preview for item photos
  - Custom site branding
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    ChatMessage,
    Claim,
    Conversation,
    FinderRating,
    FinderReputation,
    Item,
    Notification,
    OTPToken,
    Payment,
    PointTransaction,
    User,
    UserBadge,
)


# ─── User Admin ───────────────────────────────────────────────────────────────

@admin.register(User)
class FindoraUserAdmin(UserAdmin):
    """
    Admin interface for Findora users.

    Displays user-centric activity metrics (Lost reports, Found reports,
    successful returns, points, and reputation) without permanent role silos.
    """

    list_display = [
        'full_name', 'username', 'email', 'role_badge', 'account_status',
        'lost_reports_count', 'found_reports_count', 'successful_returns_count',
        'points_display', 'reputation_display',
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
        return obj.get_full_name() or obj.username

    @admin.display(description='Role')
    def role_badge(self, obj):
        colors = {
            'owner': ('#EDE9FE', '#6D28D9'),
            'finder': ('#DCFCE7', '#16A34A'),
            'admin': ('#FEF3C7', '#D97706'),
        }
        bg, fg = colors.get(obj.role, ('#F3F4F6', '#6B7280'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-weight:600">{}</span>',
            bg, fg, obj.role.capitalize()
        )

    @admin.display(description='Status')
    def account_status(self, obj):
        if obj.is_locked:
            return format_html('<span style="background:#FEE2E2;color:#DC2626;padding:2px 8px;border-radius:4px;font-weight:600">Locked</span>')
        if not obj.is_verified:
            return format_html('<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:4px;font-weight:600">Unverified</span>')
        return format_html('<span style="background:#DCFCE7;color:#16A34A;padding:2px 8px;border-radius:4px;font-weight:600">Active</span>')

    @admin.display(description='Lost Reports')
    def lost_reports_count(self, obj):
        return obj.items.filter(type='lost').count()

    @admin.display(description='Found Reports')
    def found_reports_count(self, obj):
        return obj.items.filter(type='found').count()

    @admin.display(description='Returns')
    def successful_returns_count(self, obj):
        if obj.role != 'finder':
            return '-'
        rep = getattr(obj, 'reputation', None)
        return rep.successful_returns if rep else 0

    @admin.display(description='Points')
    def points_display(self, obj):
        if obj.role != 'finder':
            return '-'
        rep = getattr(obj, 'reputation', None)
        pts = rep.total_points if rep else 0
        return format_html(
            '<span style="font-weight:700;color:#534AB7;font-size:13px">🪙 {}</span>',
            pts,
        )

    @admin.display(description='Reputation')
    def reputation_display(self, obj):
        if obj.role != 'finder':
            return '-'
        rep = getattr(obj, 'reputation', None)
        if rep and rep.rating_count > 0:
            return format_html(
                '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:4px;font-weight:600">⭐ {:.1f}</span>',
                rep.average_rating,
            )
        return format_html(
            '<span style="background:#F3F4F6;color:#6B7280;padding:2px 8px;border-radius:4px">New</span>'
        )

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
    readonly_fields = ['user', 'reported_at', 'updated_at', 'image_preview']
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
        ('Media', {
            'fields': ('image', 'image_preview'),
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
        context_role = 'Owner' if obj.type == 'lost' else 'Finder'
        return f"{obj.user.get_full_name() or obj.user.username} ({context_role})"

    @admin.display(description='Reward')
    def reward_display(self, obj):
        if obj.reward and obj.reward > 0:
            return format_html(
                '<span style="color:#16A34A;font-weight:700">Rs. {}</span>',
                obj.reward,
            )
        return '—'

    @admin.display(description='Image Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:200px;border-radius:8px;" />',
                obj.image.url,
            )
        return 'No image uploaded.'

    # ─── Bulk Actions ─────────────────────────────────────────────────────────

    @admin.action(description='Approve selected items')
    def approve_items(self, request, queryset):
        updated = queryset.update(status='approved')
        for item in queryset:
            Notification.objects.create(
                user=item.user,
                type='approved',
                message=f'Your report for "{item.title}" has been approved.',
                related_item=item,
            )
        self.message_user(request, f'{updated} item(s) approved.')

    @admin.action(description='Reject selected items')
    def reject_items(self, request, queryset):
        updated = queryset.update(status='rejected')
        for item in queryset:
            Notification.objects.create(
                user=item.user,
                type='rejected',
                message=f'Your report for "{item.title}" was rejected.',
                related_item=item,
            )
        self.message_user(request, f'{updated} item(s) rejected.')

    @admin.action(description='Mark selected items as resolved')
    def mark_resolved(self, request, queryset):
        updated = queryset.update(status='resolved')
        self.message_user(request, f'{updated} item(s) marked as resolved.')


# ─── Claim Admin ──────────────────────────────────────────────────────────────

@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    """Admin interface for managing ownership claims."""

    list_display = ['item', 'claimant', 'status', 'claimed_at']
    list_filter = ['status', 'claimed_at']
    search_fields = ['item__title', 'claimant__username', 'claimant__email', 'proof_description']
    readonly_fields = ['claimed_at']
    ordering = ['-claimed_at']
    actions = ['approve_claims', 'reject_claims']

    @admin.action(description='Approve selected claims')
    def approve_claims(self, request, queryset):
        for claim in queryset:
            claim.status = 'approved'
            claim.save()
            claim.item.status = 'resolved'
            claim.item.save()
            Notification.objects.create(
                user=claim.claimant,
                type='claim',
                message=f'Your claim on "{claim.item.title}" was approved!',
                related_item=claim.item,
            )
        self.message_user(request, f'{queryset.count()} claim(s) approved.')

    @admin.action(description='Reject selected claims')
    def reject_claims(self, request, queryset):
        updated = queryset.update(status='rejected')
        for claim in queryset:
            Notification.objects.create(
                user=claim.claimant,
                type='claim',
                message=f'Your claim on "{claim.item.title}" was rejected.',
                related_item=claim.item,
            )
        self.message_user(request, f'{updated} claim(s) rejected.')


# ─── Chat Admin ───────────────────────────────────────────────────────────────

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Chat Conversations."""
    list_display = ['id', 'item', 'owner', 'finder', 'created_at']
    search_fields = ['item__title', 'owner__username', 'finder__username']
    list_filter = ['created_at']
    ordering = ['-created_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """Admin interface for direct chat messages between users."""

    list_display = ['conversation', 'sender', 'message_preview', 'is_read', 'sent_at']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['sender__username', 'message', 'conversation__item__title']
    readonly_fields = ['conversation', 'sender', 'message', 'is_read', 'sent_at']
    ordering = ['-sent_at']

    @admin.display(description='Message Preview')
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


# ─── Reputation Admin ─────────────────────────────────────────────────────────

@admin.register(FinderReputation)
class FinderReputationAdmin(admin.ModelAdmin):
    """Admin interface for user reputations and stats."""

    list_display = [
        'user', 'points_display', 'successful_returns', 'reputation_badge',
        'rating_count', 'primary_badge', 'updated_at',
    ]
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name']
    list_filter = ['updated_at']
    ordering = ['-total_points', '-successful_returns']
    readonly_fields = ['updated_at']

    @admin.display(description='Total Points')
    def points_display(self, obj):
        return format_html(
            '<span style="font-weight:700;color:#534AB7;font-size:13px">🪙 {}</span>',
            obj.total_points,
        )

    @admin.display(description='Reputation')
    def reputation_badge(self, obj):
        if obj.rating_count > 0:
            return format_html(
                '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;'
                'border-radius:4px;font-weight:600">⭐ {:.1f}</span>',
                obj.average_rating,
            )
        return format_html(
            '<span style="background:#F3F4F6;color:#6B7280;padding:2px 8px;'
            'border-radius:4px">New</span>'
        )


@admin.register(PointTransaction)
class PointTransactionAdmin(admin.ModelAdmin):
    """Admin interface for point transactions history and auditing."""

    list_display = [
        'user', 'points_badge', 'transaction_type', 'related_item',
        'description_preview', 'created_at',
    ]
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['user__username', 'user__email', 'description', 'related_item__title']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 25
    date_hierarchy = 'created_at'

    @admin.display(description='Points')
    def points_badge(self, obj):
        if obj.points > 0:
            color = '#16A34A'
            bg = '#DCFCE7'
            sign = '+'
        elif obj.points < 0:
            color = '#DC2626'
            bg = '#FEE2E2'
            sign = ''
        else:
            color = '#6B7280'
            bg = '#F3F4F6'
            sign = ''
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;'
            'border-radius:4px;font-weight:700">{}{}</span>',
            bg, color, sign, obj.points,
        )

    @admin.display(description='Description')
    def description_preview(self, obj):
        return obj.description[:60] + '…' if len(obj.description) > 60 else obj.description


@admin.register(FinderRating)
class FinderRatingAdmin(admin.ModelAdmin):
    """Admin interface for Owner ratings and reviews."""

    list_display = ['owner', 'finder', 'item', 'rating_stars', 'review_preview', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['owner__username', 'finder__username', 'item__title', 'review']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
    list_per_page = 25

    @admin.display(description='Rating')
    def rating_stars(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        return format_html(
            '<span style="color:#D97706;font-size:14px;font-weight:600">{} ({})</span>',
            stars, obj.rating,
        )

    @admin.display(description='Review')
    def review_preview(self, obj):
        if not obj.review:
            return '—'
        return obj.review[:50] + '…' if len(obj.review) > 50 else obj.review


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    """Admin interface for unlocked user achievements."""

    list_display = ['user', 'badge_display', 'required_returns', 'earned_at']
    list_filter = ['badge_key', 'earned_at']
    search_fields = ['user__username', 'name', 'badge_key']
    readonly_fields = ['earned_at']
    ordering = ['-earned_at']

    @admin.display(description='Badge')
    def badge_display(self, obj):
        return format_html(
            '<span style="font-size:13px;font-weight:600">{} {}</span>',
            obj.icon, obj.name,
        )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for item promotion payments."""

    list_display = ['id', 'user', 'item', 'amount_display', 'provider', 'status_badge', 'created_at']
    list_filter = ['status', 'provider', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'item__title']
    readonly_fields = ['created_at', 'verified_at']
    ordering = ['-created_at']

    @admin.display(description='Amount')
    def amount_display(self, obj):
        return f"Rs. {obj.amount}"

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'PENDING': '#854F0B',
            'COMPLETED': '#1D9E75',
            'FAILED': '#D85A30',
            'CANCELLED': '#666',
        }
        color = colors.get(obj.status, '#666')
        return format_html(
            '<span style="background:{};color:white;padding:2px 8px;'
            'border-radius:4px;font-size:11px;font-weight:600">{}</span>',
            color, obj.status,
        )


# ─── Admin Site Branding ──────────────────────────────────────────────────────

admin.site.site_header = 'Findora Administration'
admin.site.site_title = 'Findora Admin'
admin.site.index_title = 'Lost & Found Management System'
