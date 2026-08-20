"""
Findora Professional Django Admin Configuration.

Implements a secure, production-ready administration system with:
  - Strict separation of Administrator accounts from Application Users (Owners & Finders)
  - Custom FindoraAdminSite with live database metrics dashboard
  - Custom ModelAdmins with status badges, thumbnail previews, and audit logging
  - Protection for destructive operations and safe bulk workflows
  - Optimized ORM queries (select_related, prefetch_related) preventing N+1 issues
"""

from decimal import Decimal
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminPasswordChangeForm
from django.contrib.auth.models import Group
from django.db.models import Sum, Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import (
    AdminAuditLog,
    Administrator,
    ChatMessage,
    Claim,
    Conversation,
    Item,
    ItemImage,
    Notification,
    OTPToken,
    Payment,
    User,
)


# ─────────────────────────────────────────────────────────────────────────────
# Audit Helper & Base Admin
# ─────────────────────────────────────────────────────────────────────────────

def log_admin_action(request, obj, action_flag, change_message=''):
    """Helper to record administrative actions in AdminAuditLog."""
    try:
        admin_user = request.user if isinstance(request.user, Administrator) else None
        admin_name = request.user.username if request.user.is_authenticated else 'System'
        ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip() or request.META.get('REMOTE_ADDR', '')
        
        AdminAuditLog.objects.create(
            admin=admin_user,
            admin_username=admin_name,
            action_flag=action_flag,
            target_model=obj._meta.verbose_name.title() if hasattr(obj, '_meta') else str(type(obj)),
            object_id=str(getattr(obj, 'pk', '')),
            object_repr=str(obj)[:200],
            change_message=change_message,
            ip_address=ip or None,
        )
    except Exception:
        pass


class FindoraBaseAdmin(admin.ModelAdmin):
    """Base ModelAdmin with integrated Findora audit logging."""

    def log_addition(self, request, object, message):
        log_admin_action(request, object, action_flag=1, change_message=f"Added: {message}")

    def log_change(self, request, object, message):
        log_admin_action(request, object, action_flag=2, change_message=f"Changed: {message}")

    def log_deletion(self, request, object, object_repr):
        log_admin_action(request, object, action_flag=3, change_message=f"Deleted: {object_repr}")


from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError


class FindoraAdminAuthenticationForm(AdminAuthenticationForm):
    """Admin login form that strictly restricts login to Administrator accounts."""

    def confirm_login_allowed(self, user):
        if not isinstance(user, Administrator):
            raise ValidationError(
                "Access denied. Only Administrator accounts are permitted to log in to Findora Admin.",
                code="not_admin",
            )
        if not user.is_active or not user.is_staff:
            raise ValidationError(
                "This administrator account is inactive or lacks staff permissions.",
                code="inactive",
            )


# ─────────────────────────────────────────────────────────────────────────────
# Custom Findora Admin Site with Real Dashboard
# ─────────────────────────────────────────────────────────────────────────────

class FindoraAdminSite(AdminSite):
    """
    Findora Custom Admin Site.

    Enforces Administrator account authentication and renders an executive
    production dashboard with live statistics from the actual database.
    """

    site_header = 'Findora Administration'
    site_title = 'Findora Admin Panel'
    index_title = 'Platform Operations & Management Dashboard'
    site_url = None  # Admin is separate from the mobile API
    login_form = FindoraAdminAuthenticationForm

    def has_permission(self, request):
        """Only active Administrator accounts can access the admin panel."""
        return bool(
            request.user
            and request.user.is_authenticated
            and isinstance(request.user, Administrator)
            and request.user.is_active
            and request.user.is_staff
        )

    def index(self, request, extra_context=None):
        """Custom dashboard view displaying live system metrics."""
        if not self.has_permission(request):
            return self.login(request)

        now = timezone.now()

        # 1. User Statistics
        total_owners = User.objects.filter(role='owner').count()
        total_finders = User.objects.filter(role='finder').count()
        active_users = User.objects.filter(is_active=True).count()
        inactive_users = User.objects.filter(is_active=False).count()
        verified_users = User.objects.filter(is_verified=True).count()
        locked_users = User.objects.filter(is_locked=True).count()
        total_admins = Administrator.objects.filter(is_active=True).count()

        # 2. Items Statistics
        total_lost = Item.objects.filter(type='lost').count()
        total_found = Item.objects.filter(type='found').count()
        pending_items = Item.objects.filter(status='pending').count()
        approved_items = Item.objects.filter(status='approved').count()
        resolved_items = Item.objects.filter(status='resolved').count()
        rejected_items = Item.objects.filter(status='rejected').count()

        # 3. Featured Listings Statistics
        active_featured = Item.objects.filter(is_featured=True, featured_until__gt=now).count()
        expired_featured = Item.objects.filter(is_featured=True, featured_until__lte=now).count()

        # 4. Payment Statistics
        total_payments = Payment.objects.count()
        successful_payments = Payment.objects.filter(status='COMPLETED').count()
        pending_payments = Payment.objects.filter(status='PENDING').count()
        failed_payments = Payment.objects.filter(status__in=['FAILED', 'CANCELLED']).count()
        revenue_data = Payment.objects.filter(status='COMPLETED').aggregate(total=Sum('amount'))
        total_revenue = revenue_data['total'] or Decimal('0.00')

        # 5. Claims & Reports
        total_claims = Claim.objects.count()
        pending_claims = Claim.objects.filter(status='pending').count()
        approved_claims = Claim.objects.filter(status='approved').count()
        rejected_claims = Claim.objects.filter(status='rejected').count()

        # 6. Communications
        total_conversations = Conversation.objects.count()
        total_messages = ChatMessage.objects.count()
        total_notifications = Notification.objects.count()
        unread_notifications = Notification.objects.filter(is_read=False).count()

        # 7. Recent Records
        recent_items = Item.objects.select_related('user').order_by('-reported_at')[:6]
        recent_users = User.objects.order_by('-created_at')[:6]
        recent_payments = Payment.objects.select_related('user', 'item').order_by('-created_at')[:6]
        recent_claims = Claim.objects.select_related('item', 'claimant').order_by('-claimed_at')[:6]
        recent_audit_logs = AdminAuditLog.objects.order_by('-action_time')[:8]

        dashboard_context = {
            # User stats
            'total_owners': total_owners,
            'total_finders': total_finders,
            'active_users': active_users,
            'inactive_users': inactive_users,
            'verified_users': verified_users,
            'locked_users': locked_users,
            'total_admins': total_admins,
            # Item stats
            'total_lost': total_lost,
            'total_found': total_found,
            'pending_items': pending_items,
            'approved_items': approved_items,
            'resolved_items': resolved_items,
            'rejected_items': rejected_items,
            # Featured & Payments
            'active_featured': active_featured,
            'expired_featured': expired_featured,
            'total_payments': total_payments,
            'successful_payments': successful_payments,
            'pending_payments': pending_payments,
            'failed_payments': failed_payments,
            'total_revenue': f"{total_revenue:,.2f}",
            # Claims
            'total_claims': total_claims,
            'pending_claims': pending_claims,
            'approved_claims': approved_claims,
            'rejected_claims': rejected_claims,
            # Communication
            'total_conversations': total_conversations,
            'total_messages': total_messages,
            'total_notifications': total_notifications,
            'unread_notifications': unread_notifications,
            # Activity feeds
            'recent_items': recent_items,
            'recent_users': recent_users,
            'recent_payments': recent_payments,
            'recent_claims': recent_claims,
            'recent_audit_logs': recent_audit_logs,
        }

        if extra_context:
            dashboard_context.update(extra_context)

        return super().index(request, extra_context=dashboard_context)


# Global Admin Site instance
admin_site = FindoraAdminSite(name='findora_admin')


# ─────────────────────────────────────────────────────────────────────────────
# 1. Administrator Account Management
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Administrator, site=admin_site)
class AdministratorAdmin(FindoraBaseAdmin):
    """
    Management interface for System Administrators.

    This section contains ONLY administrator accounts. Application users (Owners/Finders)
    never appear here. Admin passwords are fully hashed and never displayed.
    """

    list_display = [
        'username', 'email', 'full_name_display', 'admin_role_badge',
        'status_badge', 'superuser_badge', 'last_login_display', 'created_at',
    ]
    list_filter = ['admin_role', 'is_active', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    list_per_page = 20

    fieldsets = (
        ('Administrator Account', {
            'fields': ('username', 'email', 'admin_role', 'password'),
        }),
        ('Personal Details', {
            'fields': ('first_name', 'last_name', 'phone'),
        }),
        ('Access & Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Audit Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        ('Create Administrator', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'admin_role', 'first_name', 'last_name', 'phone', 'is_active', 'is_staff'),
        }),
    )

    # ─── Display Methods ──────────────────────────────────────────────────────

    @admin.display(description='Name')
    def full_name_display(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Admin Role')
    def admin_role_badge(self, obj):
        role_styles = {
            'super_admin': ('#4F46E5', '#EEF2FF', 'Super Admin'),
            'moderator': ('#059669', '#ECFDF5', 'Moderator'),
            'payment_manager': ('#D97706', '#FFFBEB', 'Payment Manager'),
            'content_manager': ('#2563EB', '#EFF6FF', 'Content Manager'),
        }
        color, bg, label = role_styles.get(obj.admin_role, ('#6B7280', '#F3F4F6', obj.admin_role))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:12px;'
            'font-size:11px;font-weight:600;display:inline-block;border:1px solid {}">{}</span>',
            bg, color, color, label,
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background:#ECFDF5;color:#059669;padding:3px 8px;border-radius:12px;'
                'font-size:11px;font-weight:600;border:1px solid #10B981">Active</span>'
            )
        return mark_safe(
            '<span style="background:#FEF2F2;color:#DC2626;padding:3px 8px;border-radius:12px;'
            'font-size:11px;font-weight:600;border:1px solid #EF4444">Inactive</span>'
        )

    @admin.display(description='Superuser')
    def superuser_badge(self, obj):
        if obj.is_superuser:
            return mark_safe('<span style="color:#4F46E5;font-weight:700">★ Full Access</span>')
        return mark_safe('<span style="color:#6B7280">Standard</span>')

    @admin.display(description='Last Login')
    def last_login_display(self, obj):
        if obj.last_login:
            return obj.last_login.strftime('%Y-%m-%d %H:%M')
        return 'Never'

    def save_model(self, request, obj, form, change):
        if not change and obj.password and not obj.password.startswith('pbkdf2_') and not obj.password.startswith('argon2'):
            obj.set_password(obj.password)
        super().save_model(request, obj, form, change)


# ─────────────────────────────────────────────────────────────────────────────
# 2. Application User Management (Owners & Finders ONLY)
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(User, site=admin_site)
class AppUserAdmin(FindoraBaseAdmin):
    """
    Management interface for Findora Application Users (Owners & Finders).

    This section contains ONLY Owner and Finder accounts.
    Administrators NEVER appear here. Deleting an Application User
    will NEVER affect or delete any Administrator account.
    """

    list_display = [
        'profile_thumbnail', 'username', 'email', 'full_name_display',
        'role_badge', 'verification_badge', 'status_badge', 'locked_badge',
        'date_joined_display',
    ]
    list_filter = ['role', 'is_verified', 'is_locked', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone', 'id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'failed_login_attempts', 'profile_image_preview']
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Account & Identity', {
            'fields': ('username', 'email', 'profile_image_preview', 'profile_image'),
        }),
        ('Personal Details', {
            'fields': ('first_name', 'last_name', 'phone', 'role'),
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',),
        }),
        ('Security & Lock Status', {
            'fields': ('is_active', 'is_verified', 'is_locked', 'locked_until', 'failed_login_attempts'),
        }),
        ('Activity Timestamps', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['verify_users', 'unlock_users', 'activate_users', 'deactivate_users']

    def get_queryset(self, request):
        """Ensure only Owner and Finder users are displayed."""
        return super().get_queryset(request).filter(role__in=['owner', 'finder'])

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Avatar')
    def profile_thumbnail(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="width:34px;height:34px;border-radius:50%;object-fit:cover;'
                'border:2px solid #E0E7FF;box-shadow:0 1px 3px rgba(0,0,0,0.1)"/>',
                obj.profile_image.url,
            )
        initials = (obj.first_name[:1] + obj.last_name[:1]).upper() or obj.username[:2].upper()
        return format_html(
            '<div style="width:34px;height:34px;border-radius:50%;background:#EEF2FF;color:#4F46E5;'
            'display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;'
            'border:1px solid #C7D2FE">{}</div>',
            initials,
        )

    @admin.display(description='Full Name')
    def full_name_display(self, obj):
        return obj.get_full_name() or '—'

    @admin.display(description='Role')
    def role_badge(self, obj):
        if obj.role == 'owner':
            return mark_safe(
                '<span style="background:#EEF2FF;color:#4F46E5;padding:3px 10px;border-radius:12px;'
                'font-size:11px;font-weight:600;border:1px solid #818CF8">Owner</span>'
            )
        elif obj.role == 'finder':
            return mark_safe(
                '<span style="background:#ECFDF5;color:#059669;padding:3px 10px;border-radius:12px;'
                'font-size:11px;font-weight:600;border:1px solid #34D399">Finder</span>'
            )
        return format_html('<span style="color:#6B7280">{}</span>', obj.role)

    @admin.display(description='Verified')
    def verification_badge(self, obj):
        if obj.is_verified:
            return mark_safe(
                '<span style="background:#ECFDF5;color:#059669;padding:2px 8px;border-radius:10px;'
                'font-size:11px;font-weight:600">✓ Verified</span>'
            )
        return mark_safe(
            '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;border-radius:10px;'
            'font-size:11px;font-weight:600">Unverified</span>'
        )

    @admin.display(description='Account Status')
    def status_badge(self, obj):
        if obj.is_active:
            return mark_safe(
                '<span style="background:#ECFDF5;color:#059669;padding:2px 8px;border-radius:10px;'
                'font-size:11px;font-weight:600">Active</span>'
            )
        return mark_safe(
            '<span style="background:#FEF2F2;color:#DC2626;padding:2px 8px;border-radius:10px;'
            'font-size:11px;font-weight:600">Inactive</span>'
        )

    @admin.display(description='Lock State')
    def locked_badge(self, obj):
        if obj.is_locked:
            return format_html(
                '<span style="background:#FEF2F2;color:#DC2626;padding:2px 8px;border-radius:10px;'
                'font-size:11px;font-weight:600">🔒 Locked</span>'
            )
        return mark_safe('<span style="color:#9CA3AF;font-size:11px">Normal</span>')

    @admin.display(description='Joined')
    def date_joined_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d') if obj.created_at else '—'

    @admin.display(description='Profile Image Preview')
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="max-height:120px;border-radius:8px;box-shadow:0 2px 6px rgba(0,0,0,0.1)"/>',
                obj.profile_image.url,
            )
        return 'No image uploaded'

    # ─── Bulk Actions ─────────────────────────────────────────────────────────

    @admin.action(description='Verify selected users')
    def verify_users(self, request, queryset):
        count = queryset.update(is_verified=True)
        for u in queryset:
            log_admin_action(request, u, action_flag=7, change_message="Marked as verified via bulk action")
        self.message_user(request, f'{count} user(s) verified successfully.')

    @admin.action(description='Unlock selected user accounts')
    def unlock_users(self, request, queryset):
        count = queryset.update(is_locked=False, failed_login_attempts=0, locked_until=None)
        for u in queryset:
            log_admin_action(request, u, action_flag=8, change_message="Unlocked account via bulk action")
        self.message_user(request, f'{count} account(s) unlocked successfully.')

    @admin.action(description='Activate selected users')
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        for u in queryset:
            log_admin_action(request, u, action_flag=2, change_message="Activated user")
        self.message_user(request, f'{count} user(s) activated.')

    @admin.action(description='Deactivate selected users')
    def deactivate_users(self, request, queryset):
        count = queryset.update(is_active=False)
        for u in queryset:
            log_admin_action(request, u, action_flag=2, change_message="Deactivated user")
        self.message_user(request, f'{count} user(s) deactivated.')


# ─────────────────────────────────────────────────────────────────────────────
# 3. Item Management (Lost & Found)
# ─────────────────────────────────────────────────────────────────────────────

class ItemImageInline(admin.TabularInline):
    """Inline photos display within the Item admin detail page."""
    model = ItemImage
    extra = 0
    readonly_fields = ['image_preview', 'uploaded_at']

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:80px;border-radius:6px;box-shadow:0 1px 4px rgba(0,0,0,0.1)"/>',
                obj.image.url,
            )
        return '—'


class ClaimInline(admin.TabularInline):
    """Inline claim display within the Item admin detail page."""
    model = Claim
    extra = 0
    readonly_fields = ['claimant', 'status', 'proof_description', 'claimed_at']
    can_delete = False
    show_change_link = True


@admin.register(Item, site=admin_site)
class ItemAdmin(FindoraBaseAdmin):
    """
    Management interface for Lost and Found item reports.

    Features query optimization (select_related/prefetch_related), status badges,
    image previews, return tracking, and inline claims.
    """

    list_display = [
        'thumbnail_preview', 'title', 'type_badge', 'category_badge',
        'status_badge', 'featured_badge', 'reporter_link', 'reward_display',
        'location', 'reported_at',
    ]
    list_filter = ['type', 'status', 'is_featured', 'category', 'reported_at']
    search_fields = ['title', 'description', 'category', 'location', 'user__username', 'user__email', 'id']
    ordering = ['-reported_at']
    readonly_fields = ['reported_at', 'updated_at', 'resolved_at', 'image_preview', 'reporter_info']
    list_per_page = 20
    date_hierarchy = 'reported_at'
    inlines = [ItemImageInline, ClaimInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'type', 'category', 'status', 'description', 'reward'),
        }),
        ('Reporter & Ownership', {
            'fields': ('user', 'reporter_info'),
        }),
        ('Location Details', {
            'fields': ('location', 'latitude', 'longitude'),
        }),
        ('Featured Listing Promotion', {
            'fields': ('is_featured', 'featured_until'),
        }),
        ('Return Lifecycle & Confirmation', {
            'fields': ('owner_returned_confirm', 'finder_returned_confirm', 'resolved_at'),
        }),
        ('Media & Photos', {
            'fields': ('image', 'image_preview'),
        }),
        ('Audit Timestamps', {
            'fields': ('reported_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    actions = ['approve_items', 'reject_items', 'mark_resolved', 'feature_items_3d', 'feature_items_7d', 'unfeature_items']

    def get_queryset(self, request):
        """Eager load relationships to eliminate N+1 queries."""
        return super().get_queryset(request).select_related('user').prefetch_related('images', 'claims')

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Photo')
    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;border-radius:6px;object-fit:cover;'
                'box-shadow:0 1px 3px rgba(0,0,0,0.12)"/>',
                obj.image.url,
            )
        first_img = obj.images.first()
        if first_img and first_img.image:
            return format_html(
                '<img src="{}" style="width:40px;height:40px;border-radius:6px;object-fit:cover;'
                'box-shadow:0 1px 3px rgba(0,0,0,0.12)"/>',
                first_img.image.url,
            )
        return mark_safe('<div style="width:40px;height:40px;border-radius:6px;background:#F3F4F6;display:flex;align-items:center;justify-content:center;color:#9CA3AF;font-size:18px">📦</div>')

    @admin.display(description='Type')
    def type_badge(self, obj):
        if obj.type == 'lost':
            return mark_safe(
                '<span style="background:#FEF2F2;color:#DC2626;padding:3px 9px;border-radius:12px;'
                'font-size:11px;font-weight:700;border:1px solid #FCA5A5">LOST</span>'
            )
        return mark_safe(
            '<span style="background:#ECFDF5;color:#059669;padding:3px 9px;border-radius:12px;'
            'font-size:11px;font-weight:700;border:1px solid #6EE7B7">FOUND</span>'
        )

    @admin.display(description='Category')
    def category_badge(self, obj):
        return format_html(
            '<span style="background:#F3F4F6;color:#374151;padding:2px 8px;border-radius:8px;'
            'font-size:11px;font-weight:500">{}</span>',
            obj.get_category_display(),
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        status_styles = {
            'pending': ('#D97706', '#FEF3C7', '#FCD34D', 'Pending Review'),
            'approved': ('#059669', '#ECFDF5', '#6EE7B7', 'Approved'),
            'resolved': ('#4F46E5', '#EEF2FF', '#A5B4FC', 'Resolved / Returned'),
            'rejected': ('#DC2626', '#FEF2F2', '#FCA5A5', 'Rejected'),
        }
        color, bg, border, label = status_styles.get(obj.status, ('#6B7280', '#F3F4F6', '#D1D5DB', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:3px 9px;border-radius:12px;'
            'font-size:11px;font-weight:600;border:1px solid {}">{}</span>',
            bg, color, border, label,
        )

    @admin.display(description='Featured')
    def featured_badge(self, obj):
        if obj.is_featured and obj.featured_until and obj.featured_until > timezone.now():
            return format_html(
                '<span style="background:#FFFBEB;color:#D97706;padding:3px 8px;border-radius:12px;'
                'font-size:11px;font-weight:700;border:1px solid #F59E0B">★ Active</span>'
            )
        elif obj.is_featured:
            return mark_safe('<span style="color:#9CA3AF;font-size:11px">Expired</span>')
        return mark_safe('<span style="color:#D1D5DB;font-size:11px">—</span>')

    @admin.display(description='Reporter')
    def reporter_link(self, obj):
        role_label = obj.user.role.upper()
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a> '
            '<span style="font-size:10px;color:#6B7280">({})</span>',
            obj.user.pk, obj.user.username, role_label,
        )

    @admin.display(description='Reward')
    def reward_display(self, obj):
        return f"Rs. {obj.reward:,.2f}" if obj.reward > 0 else '—'

    @admin.display(description='Reporter Details')
    def reporter_info(self, obj):
        return format_html(
            '<div><strong>Username:</strong> {}</div>'
            '<div><strong>Email:</strong> {}</div>'
            '<div><strong>Phone:</strong> {}</div>'
            '<div><strong>Role:</strong> {}</div>',
            obj.user.username, obj.user.email, obj.user.phone or 'N/A', obj.user.role.capitalize(),
        )

    @admin.display(description='Image Preview')
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height:220px;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.15)"/>',
                obj.image.url,
            )
        return 'No primary photo uploaded'

    # ─── Bulk Actions ─────────────────────────────────────────────────────────

    @admin.action(description='Approve selected items')
    def approve_items(self, request, queryset):
        count = queryset.update(status='approved')
        for item in queryset:
            log_admin_action(request, item, action_flag=4, change_message="Item approved")
            Notification.objects.create(
                user=item.user,
                type='approved',
                message=f'Your {item.type} report "{item.title}" has been approved and is now live.',
                related_item=item,
            )
        self.message_user(request, f'{count} item(s) approved successfully.')

    @admin.action(description='Reject selected items')
    def reject_items(self, request, queryset):
        count = queryset.update(status='rejected')
        for item in queryset:
            log_admin_action(request, item, action_flag=5, change_message="Item rejected")
            Notification.objects.create(
                user=item.user,
                type='rejected',
                message=f'Your {item.type} report "{item.title}" was rejected by moderators.',
                related_item=item,
            )
        self.message_user(request, f'{count} item(s) rejected.')

    @admin.action(description='Mark selected items as resolved')
    def mark_resolved(self, request, queryset):
        count = queryset.update(status='resolved', resolved_at=timezone.now())
        for item in queryset:
            log_admin_action(request, item, action_flag=6, change_message="Item marked resolved")
        self.message_user(request, f'{count} item(s) marked as resolved.')

    @admin.action(description='Promote to Featured (3 Days)')
    def feature_items_3d(self, request, queryset):
        until = timezone.now() + timezone.timedelta(days=3)
        count = queryset.update(is_featured=True, featured_until=until)
        for item in queryset:
            log_admin_action(request, item, action_flag=2, change_message="Featured for 3 days")
        self.message_user(request, f'{count} item(s) promoted to Featured for 3 days.')

    @admin.action(description='Promote to Featured (7 Days)')
    def feature_items_7d(self, request, queryset):
        until = timezone.now() + timezone.timedelta(days=7)
        count = queryset.update(is_featured=True, featured_until=until)
        for item in queryset:
            log_admin_action(request, item, action_flag=2, change_message="Featured for 7 days")
        self.message_user(request, f'{count} item(s) promoted to Featured for 7 days.')

    @admin.action(description='Remove from Featured')
    def unfeature_items(self, request, queryset):
        count = queryset.update(is_featured=False, featured_until=None)
        for item in queryset:
            log_admin_action(request, item, action_flag=2, change_message="Removed from Featured")
        self.message_user(request, f'{count} item(s) unfeatured.')


# ─────────────────────────────────────────────────────────────────────────────
# 4. Payment & Featured Listing Management
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Payment, site=admin_site)
class PaymentAdmin(FindoraBaseAdmin):
    """
    Management interface for Payment records and Featured Listing revenue.

    Displays gateway details, transaction IDs, verification status, and promotion durations.
    Financial records are protected against accidental modifications.
    """

    list_display = [
        'transaction_id_display', 'user_link', 'item_link', 'amount_display',
        'provider_badge', 'status_badge', 'duration_badge', 'created_at', 'verified_at',
    ]
    list_filter = ['status', 'provider', 'promotion_duration', 'created_at']
    search_fields = ['transaction_id', 'user__username', 'user__email', 'item__title', 'id']
    ordering = ['-created_at']
    readonly_fields = [
        'transaction_id', 'amount', 'currency', 'provider',
        'promotion_duration', 'created_at', 'verified_at', 'user', 'item',
    ]
    list_per_page = 20
    date_hierarchy = 'created_at'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'item')

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Transaction / Ref ID')
    def transaction_id_display(self, obj):
        tx = obj.transaction_id or f"TXN-{obj.id:06d}"
        return format_html('<span style="font-family:monospace;font-weight:600">{}</span>', tx)

    @admin.display(description='User')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.user.pk, obj.user.username,
        )

    @admin.display(description='Promoted Item')
    def item_link(self, obj):
        return format_html(
            '<a href="/admin/api/item/{}/change/" style="color:#2563EB">{}</a>',
            obj.item.pk, obj.item.title[:30],
        )

    @admin.display(description='Amount')
    def amount_display(self, obj):
        return format_html(
            '<span style="font-weight:700;color:#111827">{} {:,.2f}</span>',
            obj.currency, obj.amount,
        )

    @admin.display(description='Provider')
    def provider_badge(self, obj):
        p = obj.provider.lower()
        if 'khalti' in p:
            return format_html(
                '<span style="background:#F5F3FF;color:#5B21B6;padding:2px 8px;border-radius:10px;'
                'font-size:11px;font-weight:700;border:1px solid #C4B5FD">Khalti</span>'
            )
        elif 'esewa' in p:
            return format_html(
                '<span style="background:#ECFDF5;color:#065F46;padding:2px 8px;border-radius:10px;'
                'font-size:11px;font-weight:700;border:1px solid #6EE7B7">eSewa</span>'
            )
        return format_html('<span style="color:#6B7280">{}</span>', obj.provider.upper())

    @admin.display(description='Status')
    def status_badge(self, obj):
        status_styles = {
            'COMPLETED': ('#059669', '#ECFDF5', '#6EE7B7', 'Completed'),
            'PENDING': ('#D97706', '#FEF3C7', '#FCD34D', 'Pending'),
            'FAILED': ('#DC2626', '#FEF2F2', '#FCA5A5', 'Failed'),
            'CANCELLED': ('#6B7280', '#F3F4F6', '#D1D5DB', 'Cancelled'),
        }
        color, bg, border, label = status_styles.get(obj.status, ('#6B7280', '#F3F4F6', '#D1D5DB', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:12px;'
            'font-size:11px;font-weight:600;border:1px solid {}">{}</span>',
            bg, color, border, label,
        )

    @admin.display(description='Package')
    def duration_badge(self, obj):
        return format_html(
            '<span style="background:#EFF6FF;color:#1D4ED8;padding:2px 6px;border-radius:6px;'
            'font-size:11px;font-weight:600">{}</span>',
            obj.promotion_duration,
        )


# ─────────────────────────────────────────────────────────────────────────────
# 5. Claims & Ownership Verification
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Claim, site=admin_site)
class ClaimAdmin(FindoraBaseAdmin):
    """Admin interface for ownership claims submitted on found items."""

    list_display = ['item_link', 'claimant_link', 'proof_preview', 'status_badge', 'claimed_at']
    list_filter = ['status', 'claimed_at']
    search_fields = ['item__title', 'claimant__username', 'claimant__email', 'proof_description']
    ordering = ['-claimed_at']
    readonly_fields = ['item', 'claimant', 'claimed_at']
    list_per_page = 20

    actions = ['approve_claims', 'reject_claims']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'claimant')

    @admin.display(description='Found Item')
    def item_link(self, obj):
        return format_html(
            '<a href="/admin/api/item/{}/change/" style="font-weight:600;color:#2563EB">{}</a>',
            obj.item.pk, obj.item.title,
        )

    @admin.display(description='Claimant')
    def claimant_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.claimant.pk, obj.claimant.username,
        )

    @admin.display(description='Proof Description')
    def proof_preview(self, obj):
        desc = obj.proof_description or 'No description provided'
        return desc[:60] + ('…' if len(desc) > 60 else '')

    @admin.display(description='Status')
    def status_badge(self, obj):
        styles = {
            'pending': ('#D97706', '#FEF3C7', 'Pending Review'),
            'approved': ('#059669', '#ECFDF5', 'Approved'),
            'rejected': ('#DC2626', '#FEF2F2', 'Rejected'),
        }
        color, bg, label = styles.get(obj.status, ('#6B7280', '#F3F4F6', obj.status))
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:12px;'
            'font-size:11px;font-weight:600">{}</span>',
            bg, color, label,
        )

    @admin.action(description='Approve selected claims')
    def approve_claims(self, request, queryset):
        count = queryset.update(status='approved')
        for claim in queryset:
            claim.item.status = 'resolved'
            claim.item.resolved_at = timezone.now()
            claim.item.save(update_fields=['status', 'resolved_at'])
            log_admin_action(request, claim, action_flag=4, change_message="Claim approved")
            Notification.objects.create(
                user=claim.claimant,
                type='claim',
                message=f'Your claim on "{claim.item.title}" was approved by moderators.',
                related_item=claim.item,
            )
        self.message_user(request, f'{count} claim(s) approved.')

    @admin.action(description='Reject selected claims')
    def reject_claims(self, request, queryset):
        count = queryset.update(status='rejected')
        for claim in queryset:
            log_admin_action(request, claim, action_flag=5, change_message="Claim rejected")
            Notification.objects.create(
                user=claim.claimant,
                type='claim',
                message=f'Your claim on "{claim.item.title}" was not approved.',
                related_item=claim.item,
            )
        self.message_user(request, f'{count} claim(s) rejected.')


# ─────────────────────────────────────────────────────────────────────────────
# 6. Communication & Chat Moderation
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Conversation, site=admin_site)
class ConversationAdmin(FindoraBaseAdmin):
    """Admin interface for conversation threads between Owners and Finders."""

    list_display = ['item_link', 'owner_link', 'finder_link', 'message_count_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['item__title', 'owner__username', 'finder__username']
    ordering = ['-created_at']
    readonly_fields = ['item', 'owner', 'finder', 'created_at']
    list_per_page = 20

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item', 'owner', 'finder').annotate(msg_count=Count('messages'))

    @admin.display(description='Related Item')
    def item_link(self, obj):
        return format_html(
            '<a href="/admin/api/item/{}/change/" style="font-weight:600;color:#2563EB">{}</a>',
            obj.item.pk, obj.item.title,
        )

    @admin.display(description='Owner')
    def owner_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.owner.pk, obj.owner.username,
        )

    @admin.display(description='Finder')
    def finder_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#059669">{}</a>',
            obj.finder.pk, obj.finder.username,
        )

    @admin.display(description='Messages')
    def message_count_display(self, obj):
        count = getattr(obj, 'msg_count', obj.messages.count())
        return format_html('<span style="font-weight:600;color:#4B5563">{} msgs</span>', count)


@admin.register(ChatMessage, site=admin_site)
class ChatMessageAdmin(FindoraBaseAdmin):
    """Admin interface for chat message moderation (read-only to prevent tampering)."""

    list_display = ['conversation_link', 'sender_link', 'message_preview', 'message_type_badge', 'is_read_badge', 'sent_at']
    list_filter = ['message_type', 'is_read', 'sent_at']
    search_fields = ['sender__username', 'message', 'conversation__item__title']
    ordering = ['-sent_at']
    readonly_fields = ['conversation', 'sender', 'message', 'message_type', 'image', 'caption', 'is_read', 'sent_at']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation', 'sender', 'conversation__item')

    @admin.display(description='Conversation')
    def conversation_link(self, obj):
        if obj.conversation:
            return format_html(
                '<a href="/admin/api/conversation/{}/change/">Chat #{}: {}</a>',
                obj.conversation.pk, obj.conversation.pk, obj.conversation.item.title[:20],
            )
        return '—'

    @admin.display(description='Sender')
    def sender_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.sender.pk, obj.sender.username,
        )

    @admin.display(description='Message Preview')
    def message_preview(self, obj):
        if obj.message_type == 'image':
            return '[Photo attachment]'
        preview = obj.message[:60]
        return preview + ('…' if len(obj.message) > 60 else '')

    @admin.display(description='Type')
    def message_type_badge(self, obj):
        return obj.message_type.upper()

    @admin.display(description='Read')
    def is_read_badge(self, obj):
        if obj.is_read:
            return mark_safe('<span style="color:#059669">✓ Read</span>')
        return mark_safe('<span style="color:#9CA3AF">Unread</span>')

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 7. Notifications Management
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(Notification, site=admin_site)
class NotificationAdmin(FindoraBaseAdmin):
    """Admin interface for viewing system notifications."""

    list_display = ['user_link', 'type_badge', 'message_preview', 'is_read_badge', 'related_item_link', 'created_at']
    list_filter = ['type', 'is_read', 'created_at']
    search_fields = ['user__username', 'message']
    ordering = ['-created_at']
    readonly_fields = ['user', 'type', 'message', 'related_item', 'created_at']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'related_item')

    @admin.display(description='Recipient')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.user.pk, obj.user.username,
        )

    @admin.display(description='Type')
    def type_badge(self, obj):
        type_styles = {
            'approved': ('#059669', '#ECFDF5', 'Approved'),
            'rejected': ('#DC2626', '#FEF2F2', 'Rejected'),
            'match': ('#4F46E5', '#EEF2FF', 'Match Found'),
            'message': ('#2563EB', '#EFF6FF', 'New Message'),
            'claim': ('#D97706', '#FEF3C7', 'Claim Update'),
        }
        color, bg, label = type_styles.get(obj.type, ('#6B7280', '#F3F4F6', obj.type))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:10px;'
            'font-size:11px;font-weight:600">{}</span>',
            bg, color, label,
        )

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:70] + ('…' if len(obj.message) > 70 else '')

    @admin.display(description='Read')
    def is_read_badge(self, obj):
        return mark_safe('<span style="color:#059669">✓ Read</span>') if obj.is_read else mark_safe('<span style="color:#9CA3AF">Unread</span>')

    @admin.display(description='Related Item')
    def related_item_link(self, obj):
        if obj.related_item:
            return format_html(
                '<a href="/admin/api/item/{}/change/">{}</a>',
                obj.related_item.pk, obj.related_item.title[:25],
            )
        return '—'


# ─────────────────────────────────────────────────────────────────────────────
# 8. Security & OTP Token Audit
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(OTPToken, site=admin_site)
class OTPTokenAdmin(FindoraBaseAdmin):
    """Admin interface for OTP verification records (read-only audit)."""

    list_display = ['user_link', 'purpose_badge', 'masked_otp', 'is_used_badge', 'attempt_count', 'expires_at', 'created_at']
    list_filter = ['purpose', 'is_used', 'created_at']
    search_fields = ['user__username', 'user__email']
    ordering = ['-created_at']
    readonly_fields = ['user', 'otp_code', 'purpose', 'is_used', 'attempt_count', 'expires_at', 'created_at']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

    @admin.display(description='User')
    def user_link(self, obj):
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:600;color:#4F46E5">{}</a>',
            obj.user.pk, obj.user.email,
        )

    @admin.display(description='Purpose')
    def purpose_badge(self, obj):
        return obj.get_purpose_display()

    @admin.display(description='OTP Code')
    def masked_otp(self, obj):
        # Mask OTP for security
        return f"••{obj.otp_code[-2:]}" if len(obj.otp_code) >= 2 else "••••"

    @admin.display(description='Status')
    def is_used_badge(self, obj):
        if obj.is_used:
            return mark_safe('<span style="color:#059669">Used</span>')
        elif timezone.now() > obj.expires_at:
            return mark_safe('<span style="color:#DC2626">Expired</span>')
        return mark_safe('<span style="color:#D97706;font-weight:600">Active</span>')

    def has_add_permission(self, request):
        return False


# ─────────────────────────────────────────────────────────────────────────────
# 9. Admin Audit Logs
# ─────────────────────────────────────────────────────────────────────────────

@admin.register(AdminAuditLog, site=admin_site)
class AdminAuditLogAdmin(admin.ModelAdmin):
    """Admin interface for traceable administrator audit trail."""

    list_display = ['action_time_display', 'admin_display', 'action_badge', 'target_model', 'object_repr', 'ip_address']
    list_filter = ['action_flag', 'target_model', 'action_time']
    search_fields = ['admin__username', 'admin_username', 'object_repr', 'change_message', 'ip_address']
    ordering = ['-action_time']
    readonly_fields = ['admin', 'admin_username', 'action_time', 'action_flag', 'target_model', 'object_id', 'object_repr', 'change_message', 'ip_address']
    list_per_page = 25

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('admin')

    @admin.display(description='Time')
    def action_time_display(self, obj):
        return obj.action_time.strftime('%Y-%m-%d %H:%M:%S')

    @admin.display(description='Administrator')
    def admin_display(self, obj):
        name = obj.admin_username or (obj.admin.username if obj.admin else 'System')
        return format_html('<span style="font-weight:700;color:#4F46E5">{}</span>', name)

    @admin.display(description='Action')
    def action_badge(self, obj):
        action_styles = {
            1: ('#059669', '#ECFDF5', 'Addition'),
            2: ('#2563EB', '#EFF6FF', 'Change'),
            3: ('#DC2626', '#FEF2F2', 'Deletion'),
            4: ('#059669', '#ECFDF5', 'Approval'),
            5: ('#DC2626', '#FEF2F2', 'Rejection'),
            6: ('#4F46E5', '#EEF2FF', 'Resolution'),
            7: ('#059669', '#ECFDF5', 'Verification'),
            8: ('#D97706', '#FEF3C7', 'Lock/Unlock'),
        }
        color, bg, label = action_styles.get(obj.action_flag, ('#6B7280', '#F3F4F6', 'Action'))
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:10px;'
            'font-size:11px;font-weight:600">{}</span>',
            bg, color, label,
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
