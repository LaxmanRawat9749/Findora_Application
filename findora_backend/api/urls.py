"""
Findora API URL configuration.

All endpoints are prefixed with /api/ from the root urls.py.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # ─── Authentication ───────────────────────────────────────────────────────
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-otp/', views.VerifyOTPView.as_view(), name='verify-otp'),
    path('resend-otp/', views.ResendOTPView.as_view(), name='resend-otp'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('forgot-password/', views.ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),
    path('change-username/', views.ChangeUsernameView.as_view(), name='change-username'),

    # ─── Profile ──────────────────────────────────────────────────────────────
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/image/', views.ProfileImageView.as_view(), name='profile-image'),
    path('users/<int:pk>/public-profile/', views.PublicProfileView.as_view(), name='public-profile'),

    # ─── Items ────────────────────────────────────────────────────────────────
    path('items/', views.ItemListCreateView.as_view(), name='item-list-create'),
    path('items/resolved/', views.ResolvedItemListView.as_view(), name='item-resolved-list'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('items/<int:pk>/resolve/', views.ItemResolveView.as_view(), name='item-resolve'),

    # ─── Admin ────────────────────────────────────────────────────────────────
    path('admin/items/', views.AdminItemListView.as_view(), name='admin-item-list'),
    path('admin/items/<int:pk>/verify/', views.AdminVerifyItemView.as_view(), name='admin-verify-item'),

    # ─── Claims ───────────────────────────────────────────────────────────────
    path('claims/', views.ClaimCreateView.as_view(), name='claim-create'),

    # ─── Chat ─────────────────────────────────────────────────────────────────
    path('chat/', views.ChatListView.as_view(), name='chat'),
    path('chat/profile/', views.ChatProfileView.as_view(), name='chat-profile'),
    path('chat/message/<int:pk>/', views.ChatMessageDetailView.as_view(), name='chat-message-detail'),
    path('chat/conversation/<int:pk>/', views.ConversationDetailView.as_view(), name='chat-conversation-detail'),
    path('conversations/', views.ConversationListView.as_view(), name='conversations'),
    path('conversations/init/', views.ConversationInitView.as_view(), name='conversation-init'),

    # ─── Notifications ────────────────────────────────────────────────────────
    path('notifications/', views.NotificationListView.as_view(), name='notifications'),
    path('notifications/<int:pk>/read/', views.MarkNotificationReadView.as_view(), name='notification-read'),
]
