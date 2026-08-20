"""
Authentication backends for Findora.

Provides strict structural separation between:
1. Admin accounts (Administrator model) for Django Admin access.
2. Application users (User model: Owner & Finder) for mobile API access.
"""

import logging
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q

logger = logging.getLogger(__name__)


class AdminAuthenticationBackend(BaseBackend):
    """
    Authentication backend dedicated solely to Findora Administrator accounts.

    Used by Django Admin (/admin/) to verify admin credentials against the
    `administrators` table. Application users (Owners/Finders) CANNOT authenticate
    via this backend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from .models import Administrator

        if not username or not password:
            return None

        username = str(username).strip()

        try:
            # Allow admin login by either username or email
            admin = Administrator.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).first()

            if admin and admin.is_active and admin.check_password(password):
                logger.info("Admin login success | username=%r | id=%d", admin.username, admin.pk)
                return admin
            elif admin:
                logger.warning("Admin login failed: invalid password | username=%r", username)
        except Exception as e:
            logger.error("Admin authentication error: %s", str(e), exc_info=True)

        return None

    def get_user(self, user_id):
        from .models import Administrator

        try:
            return Administrator.objects.get(pk=user_id)
        except Administrator.DoesNotExist:
            return None


class AppUserAuthenticationBackend(BaseBackend):
    """
    Authentication backend dedicated solely to Application Users (Owners and Finders).

    Used by mobile REST API endpoints to verify credentials against the
    `users` table. Administrator accounts CANNOT authenticate via this backend.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        from .models import User

        if not username or not password:
            return None

        username = str(username).strip()

        try:
            # Match only application users (owner / finder)
            user = User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username),
                role__in=['owner', 'finder'],
            ).first()

            if user and user.is_active and not user.is_account_locked() and user.check_password(password):
                return user
        except Exception as e:
            logger.error("App user authentication error: %s", str(e), exc_info=True)

        return None

    def get_user(self, user_id):
        from .models import User

        try:
            return User.objects.get(pk=user_id, role__in=['owner', 'finder'])
        except User.DoesNotExist:
            return None
