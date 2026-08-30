"""
Findora Django Admin Configuration.

Provides a clean, streamlined, and secure management interface:
  - User Admin: Role-based list display (Owners, Finders & Admins), verification, account unlock,
    lost/found report metrics, points, and reputation ratings.
  - Item Admin: Lost & Found reports with status workflows (approval, rejection, resolution),
    reporter details, trust card, reward badges, and media previews.
  - Finder Rating Admin: Owner reviews and star ratings given to Finders for content moderation.
  - Payment Admin: Featured listing payments, status auditing, and transaction tracking.

Note: Internal technical models (PointTransaction, UserBadge, Conversation, ChatMessage,
Notification, OTPToken, Claim, FinderReputation) are managed programmatically by backend services
and APIs; their database models, tables, and logic remain 100% active and intact.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    FinderRating,
    Item,
    Notification,
    Payment,
    User,
)


# ─── User Admin ───────────────────────────────────────────────────────────────

@admin.register(User)
class FindoraUserAdmin(UserAdmin):
    """
    Admin interface for Findora users.

    Displays user-centric activity metrics (Lost reports, Found reports,
    successful returns, points, and reputation) according to Owner/Finder roles.
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
            'user': ('#E0E7FF', '#4338CA'),
        }
        bg, fg = colors.get(obj.role, ('#F3F4F6', '#6B7280'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-weight:600">{}</span>',
            bg, fg, (obj.role or 'user').capitalize()
        )

    @admin.display(description='Status')
    def account_status(self, obj):
        if obj.is_locked:
            return mark_safe('<span style="background:#FEE2E2;color:#DC2626;padding:2px 8px;border-radius:4px;font-weight:600">Locked</span>')
        if not obj.is_verified:
            return mark_safe('<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:4px;font-weight:600">Unverified</span>')
        return mark_safe('<span style="background:#DCFCE7;color:#16A34A;padding:2px 8px;border-radius:4px;font-weight:600">Active</span>')

    @admin.display(description='Lost Reports')
    def lost_reports_count(self, obj):
        return obj.items.filter(type='lost').count()

    @admin.display(description='Found Reports')
    def found_reports_count(self, obj):
        return obj.items.filter(type='found').count()

    @admin.display(description='Returns')
    def successful_returns_count(self, obj):
        rep = getattr(obj, 'reputation', None)
        return rep.successful_returns if rep else 0

    @admin.display(description='Points')
    def points_display(self, obj):
        rep = getattr(obj, 'reputation', None)
        pts = rep.total_points if rep else 0
        return format_html(
            '<span style="font-weight:700;color:#534AB7;font-size:13px">🪙 {}</span>',
            pts,
        )

    @admin.display(description='Reputation')
    def reputation_display(self, obj):
        rep = getattr(obj, 'reputation', None)
        if rep and rep.rating_count > 0:
            return format_html(
                '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:4px;font-weight:600">⭐ {}</span>',
                f"{rep.average_rating:.1f}",
            )
        return mark_safe(
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

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    """
    Admin interface for lost/found item reports.

    Features colored status and type badges, contextual reporter info (Owner/Finder),
    reporter history metrics, and item status review actions.
    """

    list_display = [
        'title', 'type_badge', 'category', 'status_badge',
        'reporter', 'location', 'reward_display', 'reported_at',
    ]
    list_filter = ['status', 'type', 'category', 'reported_at']
    search_fields = [
        'title', 'description', 'location',
        'user__username', 'user__email', 'user__first_name', 'user__last_name',
    ]
    ordering = ['-reported_at']
    readonly_fields = [
        'reporter_info_display', 'reporter_history_display',
        'reported_at', 'updated_at',
    ]
    list_per_page = 20
    date_hierarchy = 'reported_at'

    fieldsets = (
        ('Item Report Information', {
            'fields': ('user', 'type', 'title', 'description', 'category', 'reward'),
        }),
        ('Location Details', {
            'fields': ('location', 'latitude', 'longitude'),
        }),
        ('Reporter Information', {
            'fields': ('reporter_info_display',),
        }),
        ('Reporter History & Trust', {
            'fields': ('reporter_history_display',),
        }),
        ('Media', {
            'fields': ('image',),
        }),
        ('Timestamps', {
            'fields': ('reported_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status',),
            'description': 'Review all item and reporter information above before setting the item status.',
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

    @admin.display(description='Reporter Details')
    def reporter_info_display(self, obj):
        if not obj.user:
            return 'No user associated.'
        u = obj.user
        context_role = 'Owner (Lost Report)' if obj.type == 'lost' else 'Finder (Found Report)'
        role_color = '#6D28D9' if obj.type == 'lost' else '#16A34A'
        role_bg = '#EDE9FE' if obj.type == 'lost' else '#DCFCE7'
        return format_html(
            '<div style="line-height:1.7;font-size:13px;">'
            '<div><strong>Name:</strong> {}</div>'
            '<div><strong>Role for this report:</strong> '
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-weight:600">{}</span></div>'
            '<div><strong>Email:</strong> <a href="mailto:{}">{}</a></div>'
            '<div><strong>Phone:</strong> {}</div>'
            '</div>',
            u.get_full_name() or u.username,
            role_bg, role_color, context_role,
            u.email, u.email,
            u.phone or 'N/A',
        )

    @admin.display(description='Reporter History')
    def reporter_history_display(self, obj):
        if not obj.user:
            return 'No user associated.'
        u = obj.user
        rep = getattr(u, 'reputation', None)
        lost_count = u.items.filter(type='lost').count()
        found_count = u.items.filter(type='found').count()
        returns_count = rep.successful_returns if rep else 0
        points = rep.total_points if rep else 0
        rating_display = f"⭐ {rep.average_rating:.1f} ({rep.rating_count} reviews)" if rep and rep.rating_count > 0 else "New / Unrated"

        return format_html(
            '<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;">'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
            '<div style="color:#64748B;font-size:11px;">Lost Reports</div>'
            '<div style="font-size:16px;font-weight:700;color:#0F172A;">{}</div>'
            '</div>'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
            '<div style="color:#64748B;font-size:11px;">Found Reports</div>'
            '<div style="font-size:16px;font-weight:700;color:#0F172A;">{}</div>'
            '</div>'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
            '<div style="color:#64748B;font-size:11px;">Successful Returns</div>'
            '<div style="font-size:16px;font-weight:700;color:#16A34A;">{}</div>'
            '</div>'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
            '<div style="color:#64748B;font-size:11px;">Reputation</div>'
            '<div style="font-size:14px;font-weight:700;color:#D97706;">{}</div>'
            '</div>'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
            '<div style="color:#64748B;font-size:11px;">Points</div>'
            '<div style="font-size:16px;font-weight:700;color:#534AB7;">🪙 {}</div>'
            '</div>'
            '</div>',
            lost_count,
            found_count,
            returns_count,
            rating_display,
            points,
        )

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


# ─── Finder Rating Admin ──────────────────────────────────────────────────────

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


# ─── Payment Admin ────────────────────────────────────────────────────────────

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
