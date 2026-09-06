"""
Findora API URL configuration.

All endpoints are prefixed with /api/ from the root urls.py.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views
from . import payment_views

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
    path('profile/items/', views.MyReportsView.as_view(), name='my-reports'),
    path('users/<int:pk>/public-profile/', views.PublicProfileView.as_view(), name='public-profile'),

    # ─── Items ────────────────────────────────────────────────────────────────
    path('items/', views.ItemListCreateView.as_view(), name='item-list-create'),
    path('items/<int:pk>/', views.ItemDetailView.as_view(), name='item-detail'),
    path('items/<int:pk>/mark-returned/', views.MarkItemReturnedView.as_view(), name='item-mark-returned'),
    path('items/<int:pk>/confirm-return/', views.ConfirmItemReturnView.as_view(), name='item-confirm-return'),

    # ─── Admin ────────────────────────────────────────────────────────────────
    path('admin/items/', views.AdminItemListView.as_view(), name='admin-item-list'),
    path('admin/items/<int:pk>/verify/', views.AdminVerifyItemView.as_view(), name='admin-verify-item'),

    # ─── Payments ─────────────────────────────────────────────────────────────
    path('payments/initiate/', payment_views.InitiatePaymentView.as_view(), name='payment-initiate'),
    path('payments/verify/', payment_views.VerifyPaymentView.as_view(), name='payment-verify'),
    path('payments/callback/', payment_views.PaymentCallbackView.as_view(), name='payment-callback'),
    path('payments/esewa/form/<int:payment_id>/', payment_views.EsewaFormView.as_view(), name='esewa-form'),
    path('payments/esewa/verify-callback/', payment_views.EsewaVerifyCallbackView.as_view(), name='esewa-verify-callback'),

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

    # ─── Reputation & Points ──────────────────────────────────────────────────
    path('reputation/me/', views.ReputationProfileView.as_view(), name='reputation-me'),
    path('reputation/history/', views.PointHistoryView.as_view(), name='reputation-history'),
    path('reputation/rate/', views.RateFinderView.as_view(), name='reputation-rate'),
    path('reputation/rating-status/', views.RatingStatusView.as_view(), name='reputation-rating-status'),
]
