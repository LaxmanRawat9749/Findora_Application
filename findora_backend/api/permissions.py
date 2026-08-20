"""
Custom DRF permission classes for Findora.

These supplement Django REST Framework's built-in permissions with
Findora-specific role and verification checks.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission that allows only the item's owner to
    perform write operations (PUT, PATCH, DELETE).

    Any authenticated user may perform safe (read-only) operations.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.user == request.user


class IsAdminRole(BasePermission):
    """
    View-level permission that restricts access to administrators.
    """

    def has_permission(self, request, view):
        from .models import Administrator
        if not request.user or not request.user.is_authenticated:
            return False
        if isinstance(request.user, Administrator) and request.user.is_active:
            return True
        return getattr(request.user, 'is_staff', False) or getattr(request.user, 'role', None) == 'admin'


class IsVerifiedUser(BasePermission):
    """
    View-level permission that requires the authenticated user to
    have completed email verification (is_verified=True).
    """

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_verified
        )
