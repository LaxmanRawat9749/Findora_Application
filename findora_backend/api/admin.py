"""
Findora Django Admin Configuration.

Provides a unified, streamlined, and secure management interface:
  - User Admin: Role-based list display (Owners, Finders & Admins), verification, account unlock,
    lost/found report metrics, points, and reputation summary card.
  - Item Admin: Lost & Found reports with status workflows (approval, rejection, resolution),
    reporter details, trust card, reward badges, and media previews.
  - Finder Ratings & Reputation: Combined feature managing Finder performance, average star ratings,
    rating counts, successful returns, total points, badges, and complete owner reviews history.
  - Payment Admin: Featured listing payments, status auditing, and transaction tracking.

Note: Internal technical models (PointTransaction, UserBadge, Conversation, ChatMessage,
Notification, OTPToken, Claim) are managed programmatically by backend services
and APIs; their database models, tables, and logic remain 100% active and intact.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import (
    ChatMessage,
    FinderRating,
    FinderReputation,
    Item,
    ItemImage,
    Notification,
    Payment,
    User,
)

# Custom display names for combined Finder Rating & Reputation feature
FinderReputation._meta.verbose_name = 'Finder Rating & Reputation'
FinderReputation._meta.verbose_name_plural = 'Finder Ratings & Reputation'


# ─── User Admin ───────────────────────────────────────────────────────────────

@admin.register(User)
class FindoraUserAdmin(UserAdmin):
    """
    Admin interface for Findora users.

    Displays user-centric activity metrics (Lost reports, Found reports,
    successful returns, points, and reputation) according to Owner/Finder roles.
    """

    list_display = [
        'avatar_preview', 'full_name', 'username', 'email', 'role_badge', 'account_status',
        'lost_reports_count', 'found_reports_count', 'successful_returns_count',
        'points_display', 'reputation_display',
        'is_active', 'created_at',
    ]
    list_filter = ['role', 'is_verified', 'is_locked', 'is_active', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    readonly_fields = [
        'profile_image_display',
        'created_at', 'updated_at', 'last_login', 'failed_login_attempts',
        'finder_performance_summary',
    ]
    list_per_page = 25
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Account Info', {
            'fields': ('username', 'email'),
        }),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'phone', 'role', 'profile_image_display'),
        }),
        ('Status & Security', {
            'fields': (
                'is_active', 'is_verified', 'failed_login_attempts',
            ),
        }),
        ('Finder Performance (Ratings & Reputation)', {
            'fields': ('finder_performance_summary',),
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

    def _user_has_finder_activity(self, user):
        """
        Check if the user has participated as a Finder or has Finder reputation data:
          - user role is 'finder'
          - user has submitted found item reports
          - user has received owner ratings
          - user has active finder reputation (points, returns, reviews)
          - user has unlocked badges
        """
        if not user or not user.pk:
            return False
        if getattr(user, 'role', '') == 'finder':
            return True
        if user.items.filter(type='found').exists():
            return True
        if hasattr(user, 'ratings_received') and user.ratings_received.exists():
            return True
        rep = getattr(user, 'reputation', None)
        if rep and (rep.total_points > 0 or rep.successful_returns > 0 or rep.rating_count > 0):
            return True
        if hasattr(user, 'badges') and user.badges.exists():
            return True
        return False

    def get_fieldsets(self, request, obj=None):
        """
        Dynamically include the 'Finder Performance (Ratings & Reputation)' fieldset
        only when the user has Finder activity/reputation data. For Owner-only users with
        no Finder activity, the section is completely excluded.
        """
        if not obj:
            return self.add_fieldsets

        fieldsets = [
            ('Account Info', {
                'fields': ('username', 'email'),
            }),
            ('Personal Info', {
                'fields': ('first_name', 'last_name', 'phone', 'role', 'profile_image_display'),
            }),
            ('Status & Security', {
                'fields': (
                    'is_active', 'is_verified', 'failed_login_attempts',
                ),
            }),
        ]

        if self._user_has_finder_activity(obj):
            fieldsets.append(
                ('Finder Performance (Ratings & Reputation)', {
                    'fields': ('finder_performance_summary',),
                })
            )

        fieldsets.extend([
            ('Permissions', {
                'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions'),
                'classes': ('collapse',),
            }),
            ('Timestamps', {
                'fields': ('last_login', 'created_at', 'updated_at'),
                'classes': ('collapse',),
            }),
        ])

        return tuple(fieldsets)

    add_fieldsets = (
        ('Create User', {
            'classes': ('wide',),
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone', 'role', 'password1', 'password2'),
        }),
    )

    actions = ['verify_users', 'unlock_users', 'deactivate_users', 'activate_users']

    # ─── Computed Columns ─────────────────────────────────────────────────────

    @admin.display(description='Photo')
    def avatar_preview(self, obj):
        if obj.profile_image and hasattr(obj.profile_image, 'url'):
            try:
                url = obj.profile_image.url
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer" title="Click to view photo">'
                    '<img src="{}" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:1px solid #E2E8F0;box-shadow:0 1px 2px rgba(0,0,0,0.06);vertical-align:middle;display:block;" alt="{}" />'
                    '</a>',
                    url, url, obj.username,
                )
            except ValueError:
                pass
        initial = (obj.first_name[:1] or obj.username[:1]).upper()
        return format_html(
            '<div style="width:36px;height:36px;border-radius:50%;background:#E2E8F0;display:inline-flex;align-items:center;justify-content:center;color:#64748B;font-size:12px;font-weight:700;">{}</div>',
            initial,
        )

    @admin.display(description='Profile Image')
    def profile_image_display(self, obj):
        if not obj or not obj.profile_image:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;">No profile photo uploaded.</span>')
        try:
            url = obj.profile_image.url
            return format_html(
                '<div style="margin-top:4px;">'
                '<a href="{}" target="_blank" rel="noopener noreferrer" title="Click to view full photo">'
                '<img src="{}" style="width:120px;height:120px;border-radius:50%;border:2px solid #E2E8F0;object-fit:cover;box-shadow:0 2px 6px rgba(0,0,0,0.08);" alt="{}" />'
                '</a>'
                '<div style="font-size:11px;color:#64748B;margin-top:6px;">Click photo to open full resolution</div>'
                '</div>',
                url, url, obj.username,
            )
        except ValueError:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;">No profile photo uploaded.</span>')

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

    @admin.display(description='Finder Performance Summary')
    def finder_performance_summary(self, obj):
        rep = getattr(obj, 'reputation', None)
        pts = rep.total_points if rep else 0
        returns = rep.successful_returns if rep else 0
        rating_count = rep.rating_count if rep else 0
        avg_rating = f"{rep.average_rating:.1f}" if rep and rep.rating_count > 0 else "New / Unrated"
        primary_badge = rep.primary_badge if rep and rep.primary_badge else "None"

        rep_link = f"/admin/api/finderreputation/{rep.id}/change/" if rep else "/admin/api/finderreputation/"

        return format_html(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:8px;font-size:13px;max-width:600px;line-height:1.7;">'
            '<div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:10px;">'
            '<div><span style="color:#64748B;font-size:11px;display:block;">Average Rating</span><strong style="color:#D97706;font-size:15px;">⭐ {}</strong> ({} reviews)</div>'
            '<div><span style="color:#64748B;font-size:11px;display:block;">Successful Returns</span><strong style="color:#16A34A;font-size:15px;">{}</strong></div>'
            '<div><span style="color:#64748B;font-size:11px;display:block;">Total Points</span><strong style="color:#534AB7;font-size:15px;">🪙 {}</strong></div>'
            '<div><span style="color:#64748B;font-size:11px;display:block;">Primary Badge</span><strong style="color:#0F172A;font-size:13px;">🏅 {}</strong></div>'
            '</div>'
            '<div><a href="{}" style="color:#4F46E5;font-weight:600;text-decoration:underline;">👉 View Details & Rating History in Finder Ratings & Reputation</a></div>'
            '</div>',
            avg_rating, rating_count,
            returns,
            pts,
            primary_badge,
            rep_link
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
        'reported_image_display', 'reporter_info_display', 'reporter_history_display',
        'reported_at', 'updated_at',
    ]
    list_per_page = 20
    date_hierarchy = 'reported_at'

    fieldsets = (
        ('Item Report Information', {
            'fields': ('user', 'type', 'title', 'description', 'category', 'reward'),
        }),
        ('Reported Item Image', {
            'fields': ('reported_image_display',),
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
        ('Timestamps', {
            'fields': ('reported_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Status', {
            'fields': ('status',),
            'description': 'Review all item and reporter information above before setting the item status.',
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """
        Make 'user' read-only on the Change Item form (when obj exists) to remove
        the interactive Foreign Key controls (pencil, +, eye, dropdown) while keeping
        the User field and username cleanly visible and informational.
        """
        ro = list(super().get_readonly_fields(request, obj))
        if obj and 'user' not in ro:
            ro.append('user')
        return ro

    def get_fieldsets(self, request, obj=None):
        """
        Dynamically adjust fieldsets based on Item report type:
        - Owner / Lost item (type='lost'): includes 'reward' so owners/admins can manage lost item rewards.
        - Finder / Found item (type='found'): excludes 'reward' because found item reports do not have rewards.
        """
        if obj and obj.type == 'found':
            return (
                ('Item Report Information', {
                    'fields': ('user', 'type', 'title', 'description', 'category'),
                }),
                ('Reported Item Image', {
                    'fields': ('reported_image_display',),
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
                ('Timestamps', {
                    'fields': ('reported_at', 'updated_at'),
                    'classes': ('collapse',),
                }),
                ('Status', {
                    'fields': ('status',),
                    'description': 'Review all item and reporter information above before setting the item status.',
                }),
            )
        return super().get_fieldsets(request, obj)

    actions = ['approve_items', 'reject_items', 'mark_resolved']

    # ─── Computed Columns & Display Methods ───────────────────────────────────

    @admin.display(description='Reported Item Image')
    def reported_image_display(self, obj):
        """
        Display the actual image uploaded during the report for this exact Item.
        Directly looks up this Item's exact image reference (obj.image or obj.images).
        Never mixes Owner/Finder images, never uses category/title fallbacks or default placeholder images.
        """
        if not obj or not obj.pk:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;">No image</span>')

        image_field = None
        if obj.image and hasattr(obj.image, 'name') and obj.image.name:
            image_field = obj.image
        else:
            first_img = obj.images.filter(item_id=obj.id).order_by('uploaded_at', 'id').first()
            if first_img and first_img.image and hasattr(first_img.image, 'name') and first_img.image.name:
                image_field = first_img.image

        # If no image is associated in database
        if not image_field:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;font-weight:500;">No image</span>')

        # Check if the physical file actually exists in storage / filesystem
        file_exists = False
        try:
            if hasattr(image_field, 'storage') and image_field.storage:
                file_exists = image_field.storage.exists(image_field.name)
            else:
                file_exists = True
        except Exception:
            file_exists = False

        if not file_exists:
            return mark_safe('<span style="color:#DC2626;font-size:13px;font-weight:500;">Image unavailable</span>')

        # Resolve image URL
        try:
            url = image_field.url
        except Exception:
            return mark_safe('<span style="color:#DC2626;font-size:13px;font-weight:500;">Image unavailable</span>')

        return format_html(
            '<div style="margin-top:4px;">'
            '<a href="{}" target="_blank" rel="noopener noreferrer" title="Click to open full-size image">'
            '<img src="{}" style="max-width:320px;max-height:320px;border-radius:8px;border:1px solid #E2E8F0;box-shadow:0 2px 8px rgba(0,0,0,0.08);object-fit:contain;background:#F8FAFC;display:block;" alt="{}" />'
            '</a>'
            '<div style="font-size:11px;color:#64748B;margin-top:6px;">Click image to open full resolution in a new tab</div>'
            '</div>',
            url,
            url,
            obj.title,
        )

    # Alias for backward compatibility
    image_display = reported_image_display

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
        if not obj or not obj.user:
            return 'No user associated.'
        u = obj.user

        if getattr(obj, 'type', '') == 'lost':
            lost_count = u.items.filter(type='lost').count()
            return format_html(
                '<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;">'
                '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:8px 12px;border-radius:6px;min-width:110px;">'
                '<div style="color:#64748B;font-size:11px;">Lost Reports</div>'
                '<div style="font-size:16px;font-weight:700;color:#0F172A;">{}</div>'
                '</div>'
                '</div>',
                lost_count,
            )

        rep = getattr(u, 'reputation', None)
        found_count = u.items.filter(type='found').count()
        returns_count = rep.successful_returns if rep else 0
        points = rep.total_points if rep else 0
        rating_display = f"⭐ {rep.average_rating:.1f} ({rep.rating_count} reviews)" if rep and rep.rating_count > 0 else "New / Unrated"

        return format_html(
            '<div style="display:flex;gap:12px;flex-wrap:wrap;font-size:12px;">'
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


# ─── Finder Ratings & Reputation Admin ────────────────────────────────────────

@admin.register(FinderReputation)
class FinderReputationAdmin(admin.ModelAdmin):
    """
    Unified Admin interface for Finder Ratings & Reputation.

    Combines:
      - Finder identification & account link
      - Average Rating ⭐, Total Ratings Count
      - Successful Returns count & Trust status
      - Total Points 🪙
      - Primary and unlocked milestone Badges
      - Full breakdown of Owner ratings & review comments
    """

    list_display = [
        'finder_display', 'average_rating_display', 'rating_count',
        'successful_returns', 'points_display', 'trust_status_badge',
        'primary_badge_display', 'updated_at',
    ]
    list_filter = ['rating_count', 'successful_returns', 'updated_at']
    search_fields = [
        'user__username', 'user__email', 'user__first_name',
        'user__last_name', 'user__phone',
    ]
    ordering = ['-average_rating', '-rating_count', '-total_points', '-successful_returns']
    readonly_fields = [
        'finder_account_card', 'average_rating_display', 'rating_count',
        'rating_sum', 'successful_returns', 'total_points',
        'trust_status_badge', 'primary_badge_display',
        'rating_history_display', 'badges_unlocked_display', 'updated_at',
    ]
    list_per_page = 25
    date_hierarchy = 'updated_at'

    fieldsets = (
        ('Finder Account Profile', {
            'fields': ('finder_account_card',),
            'description': 'User acting as Finder for found item reports and completed returns.',
        }),
        ('Performance, Ratings & Points Metrics', {
            'fields': (
                ('average_rating_display', 'rating_count', 'rating_sum'),
                ('successful_returns', 'total_points'),
                ('trust_status_badge', 'primary_badge_display'),
            ),
        }),
        ('Owner Ratings & Reviews History', {
            'fields': ('rating_history_display',),
            'description': 'Direct feedback, star ratings, and review comments submitted by Owners after returns.',
        }),
        ('Milestone Badges Unlocked', {
            'fields': ('badges_unlocked_display',),
        }),
        ('Timestamps', {
            'fields': ('updated_at',),
            'classes': ('collapse',),
        }),
    )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Finder Rating & Reputation'
        return super().changelist_view(request, extra_context=extra_context)

    def has_add_permission(self, request):
        """Reputations are generated and updated automatically by Findora services."""
        return False

    def get_queryset(self, request):
        """
        Auto-ensures active finders have a reputation record and optimizes ORM queries
        with select_related and prefetch_related.
        """
        finder_users = User.objects.filter(
            Q(role='finder') | Q(items__type='found') | Q(ratings_received__isnull=False)
        ).distinct()
        for u in finder_users:
            if not hasattr(u, 'reputation'):
                FinderReputation.objects.get_or_create(user=u)

        return super().get_queryset(request).select_related('user').prefetch_related(
            'user__badges', 'user__ratings_received', 'user__ratings_received__owner', 'user__ratings_received__item'
        )

    # ─── Computed Columns & Display Methods ───────────────────────────────────

    @admin.display(description='Finder', ordering='user__username')
    def finder_display(self, obj):
        u = obj.user
        full_name = u.get_full_name() or u.username
        return format_html(
            '<a href="/admin/api/user/{}/change/" style="font-weight:700;color:#4F46E5;">{}</a> '
            '<span style="color:#64748B;font-size:12px;">(@{})</span>',
            u.id, full_name, u.username
        )

    @admin.display(description='Average Rating', ordering='average_rating')
    def average_rating_display(self, obj):
        if obj.rating_count > 0:
            stars = '★' * int(round(obj.average_rating)) + '☆' * (5 - int(round(obj.average_rating)))
            return format_html(
                '<span style="background:#FEF3C7;color:#D97706;padding:2px 8px;'
                'border-radius:4px;font-weight:700">⭐ {:.1f}</span> '
                '<span style="color:#D97706;font-size:11px;">{}</span>',
                obj.average_rating, stars
            )
        return mark_safe(
            '<span style="background:#F3F4F6;color:#6B7280;padding:2px 8px;border-radius:4px">New / Unrated</span>'
        )

    @admin.display(description='Points', ordering='total_points')
    def points_display(self, obj):
        return format_html(
            '<span style="font-weight:700;color:#534AB7;font-size:13px">🪙 {}</span>',
            obj.total_points,
        )

    @admin.display(description='Reputation Status')
    def trust_status_badge(self, obj):
        if obj.is_trusted_finder:
            return mark_safe(
                '<span style="background:#DCFCE7;color:#16A34A;padding:3px 10px;border-radius:12px;font-weight:700;font-size:11px;">🛡️ Trusted Finder</span>'
            )
        if obj.successful_returns > 0:
            return mark_safe(
                '<span style="background:#EFF6FF;color:#2563EB;padding:3px 10px;border-radius:12px;font-weight:600;font-size:11px;">Active Finder</span>'
            )
        return mark_safe(
            '<span style="background:#F3F4F6;color:#6B7280;padding:3px 10px;border-radius:12px;font-size:11px;">New Finder</span>'
        )

    @admin.display(description='Primary Badge')
    def primary_badge_display(self, obj):
        badge = obj.primary_badge
        if badge:
            return format_html(
                '<span style="font-weight:600;color:#0F172A;">🏅 {}</span>',
                badge
            )
        return mark_safe('<span style="color:#94A3B8;">—</span>')

    @admin.display(description='Finder Profile Card')
    def finder_account_card(self, obj):
        u = obj.user
        full_name = u.get_full_name() or u.username
        role_label = (u.role or 'user').capitalize()
        return format_html(
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;padding:14px;border-radius:8px;line-height:1.8;font-size:13px;max-width:550px;">'
            '<div><strong>User:</strong> <a href="/admin/api/user/{}/change/" style="font-weight:700;color:#4F46E5;font-size:14px;">{} (@{})</a></div>'
            '<div><strong>Email:</strong> <a href="mailto:{}">{}</a></div>'
            '<div><strong>Phone:</strong> {}</div>'
            '<div><strong>Account Role:</strong> <span style="background:#EDE9FE;color:#6D28D9;padding:2px 8px;border-radius:4px;font-weight:600">{}</span></div>'
            '<div><strong>Member Since:</strong> {}</div>'
            '</div>',
            u.id, full_name, u.username,
            u.email, u.email,
            u.phone or 'N/A',
            role_label,
            u.created_at.strftime('%b %d, %Y') if u.created_at else '—'
        )

    @admin.display(description='Owner Ratings & Reviews')
    def rating_history_display(self, obj):
        ratings = obj.user.ratings_received.select_related('owner', 'item').order_by('-created_at')
        if not ratings.exists():
            return mark_safe('<p style="color:#64748B;font-style:italic;">No owner ratings received yet.</p>')

        rows = []
        for r in ratings:
            owner_name = r.owner.get_full_name() or r.owner.username
            item_title = r.item.title if r.item else '—'
            stars = '★' * r.rating + '☆' * (5 - r.rating)
            review_text = format_html('"{}"', r.review) if r.review else mark_safe('<span style="color:#94A3B8;font-style:italic;">No written review</span>')
            date_str = r.created_at.strftime('%b %d, %Y, %I:%M %p')

            rows.append(format_html(
                '<tr style="border-bottom:1px solid #E2E8F0;">'
                '<td style="padding:10px 12px;font-weight:600;"><a href="/admin/api/user/{}/change/" style="color:#4F46E5;">{}</a></td>'
                '<td style="padding:10px 12px;"><a href="/admin/api/item/{}/change/" style="color:#0F172A;font-weight:500;">{}</a></td>'
                '<td style="padding:10px 12px;color:#D97706;font-size:14px;font-weight:700;">{} ({})</td>'
                '<td style="padding:10px 12px;color:#334155;max-width:300px;">{}</td>'
                '<td style="padding:10px 12px;color:#64748B;font-size:12px;">{}</td>'
                '</tr>',
                r.owner.id, owner_name,
                r.item.id if r.item else '', item_title,
                stars, r.rating,
                review_text,
                date_str,
            ))

        return format_html(
            '<table style="width:100%;border-collapse:collapse;font-size:13px;background:#FFFFFF;border:1px solid #E2E8F0;border-radius:6px;overflow:hidden;">'
            '<thead>'
            '<tr style="background:#F8FAFC;text-align:left;border-bottom:2px solid #E2E8F0;color:#475569;font-size:12px;text-transform:uppercase;">'
            '<th style="padding:10px 12px;">Owner (Rated By)</th>'
            '<th style="padding:10px 12px;">Related Item</th>'
            '<th style="padding:10px 12px;">Rating</th>'
            '<th style="padding:10px 12px;">Review Comment</th>'
            '<th style="padding:10px 12px;">Date</th>'
            '</tr>'
            '</thead>'
            '<tbody>'
            '{}'
            '</tbody>'
            '</table>',
            mark_safe(''.join(rows))
        )

    @admin.display(description='Unlocked Milestone Badges')
    def badges_unlocked_display(self, obj):
        badges = obj.user.badges.all().order_by('required_returns')
        if not badges.exists():
            return mark_safe('<p style="color:#64748B;font-style:italic;">No badges unlocked yet.</p>')

        chips = []
        for b in badges:
            date_str = b.earned_at.strftime('%b %d, %Y')
            chips.append(format_html(
                '<div style="background:#F0FDF4;border:1px solid #BBF7D0;padding:8px 14px;border-radius:8px;display:inline-flex;align-items:center;gap:8px;margin-right:8px;margin-bottom:8px;">'
                '<span style="font-size:22px;">{}</span>'
                '<div>'
                '<div style="font-weight:700;color:#166534;font-size:13px;">{}</div>'
                '<div style="font-size:11px;color:#15803D;">{} (Earned {})</div>'
                '</div>'
                '</div>',
                b.icon, b.name, b.description, date_str
            ))
        return mark_safe(''.join(chips))


# ─── Payment Admin ────────────────────────────────────────────────────────────

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for item promotion payments."""

    list_display = ['id', 'user', 'item', 'amount_display', 'provider', 'status_badge', 'created_at']
    list_filter = ['status', 'provider', 'created_at']
    search_fields = ['user__username', 'transaction_id', 'item__title']
    readonly_fields = ['created_at', 'verified_at']
    ordering = ['-created_at']

    def has_add_permission(self, request):
        """Payments are created programmatically via payment gateways (eSewa / Khalti)."""
        return False

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


# ─── Chat Message Admin ───────────────────────────────────────────────────────

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """
    Admin interface for inspecting chat messages and uploaded chat media.
    """
    list_display = [
        'id', 'chat_media_preview', 'sender', 'conversation', 'message_type',
        'message_snippet', 'sent_at', 'is_read',
    ]
    list_filter = ['message_type', 'is_read', 'sent_at']
    search_fields = ['sender__username', 'sender__email', 'message', 'caption']
    ordering = ['-sent_at']
    readonly_fields = ['chat_media_display', 'sent_at']
    list_per_page = 25

    @admin.display(description='Media')
    def chat_media_preview(self, obj):
        if obj.image and hasattr(obj.image, 'url'):
            try:
                url = obj.image.url
                return format_html(
                    '<a href="{}" target="_blank" rel="noopener noreferrer" title="Click to view full image">'
                    '<img src="{}" style="width:40px;height:40px;border-radius:6px;object-fit:cover;border:1px solid #E2E8F0;" alt="Chat Image" />'
                    '</a>',
                    url, url,
                )
            except ValueError:
                pass
        return mark_safe('<span style="color:#94A3B8;font-size:12px;">—</span>')

    @admin.display(description='Chat Image')
    def chat_media_display(self, obj):
        if not obj or not obj.image:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;">No image attached.</span>')
        try:
            url = obj.image.url
            return format_html(
                '<a href="{}" target="_blank" rel="noopener noreferrer" title="Click to view full image">'
                '<img src="{}" style="max-width:280px;max-height:280px;border-radius:8px;border:1px solid #E2E8F0;" alt="Chat Image" />'
                '</a>',
                url, url,
            )
        except ValueError:
            return mark_safe('<span style="color:#94A3B8;font-size:13px;">No image attached.</span>')

    @admin.display(description='Message')
    def message_snippet(self, obj):
        if obj.message:
            return obj.message[:60]
        if obj.caption:
            return f"[Image] {obj.caption[:50]}"
        return "[Image]"


# ─── Admin Site Branding ──────────────────────────────────────────────────────

admin.site.site_header = 'Findora Administration'
admin.site.site_title = 'Findora Admin'
admin.site.index_title = 'Lost & Found Management System'


