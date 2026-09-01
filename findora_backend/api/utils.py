"""
OTP utility functions for Findora.

Provides helpers for generating, creating, sending, and verifying
one-time passwords used in email verification and password reset flows.
"""

import logging
import re
import secrets
import string
import threading

from django.db.models import Q
from django.utils import timezone

from .models import OTPToken

logger = logging.getLogger(__name__)


def generate_otp(length=6):
    """Generate a cryptographically secure numeric OTP of given length."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def create_otp(user, purpose):
    """
    Invalidate all previous active OTPs for this user + purpose,
    then create and return a new OTP that expires in 10 minutes.
    """
    # Mark all prior active OTPs as used so only one is valid at a time
    OTPToken.objects.filter(
        user=user,
        purpose=purpose,
        is_used=False,
    ).update(is_used=True)

    otp_code = generate_otp()
    otp = OTPToken.objects.create(
        user=user,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=timezone.now() + timezone.timedelta(minutes=10),
    )
    return otp


def send_otp_email(user, otp_code, purpose):
    """
    Send a beautifully formatted OTP email to the user for the given purpose
    using the Brevo Transactional Email API.

    The email is dispatched in a background thread so that HTTP responses are
    never blocked waiting for the external API request.
    """
    subjects = {
        'email_verify': 'Findora — Verify Your Email',
        'password_reset': 'Findora — Password Reset OTP',
    }

    subject = subjects.get(purpose, 'Findora OTP')
    recipient = user.email
    name = user.first_name or user.username

    # Define content depending on the purpose
    if purpose == 'email_verify':
        instruction_text = "Please verify your email address to complete your Findora account setup."
        text_body = (
            f"Hello {name},\n\n"
            f"Your email verification OTP is: {otp_code}\n\n"
            f"This OTP expires in 10 minutes.\n"
            f"Do not share this OTP with anyone.\n\n"
            f"— Findora Team"
        )
    else:
        instruction_text = "You requested a password reset for your Findora account."
        text_body = (
            f"Hello {name},\n\n"
            f"Your password reset OTP is: {otp_code}\n\n"
            f"This OTP expires in 10 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"— Findora Team"
        )

    # Gorgeous HTML email body
    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      background-color: #f4f5f7;
      margin: 0;
      padding: 0;
      -webkit-font-smoothing: antialiased;
    }}
    .wrapper {{
      width: 100%;
      table-layout: fixed;
      background-color: #f4f5f7;
      padding: 40px 0;
    }}
    .container {{
      max-width: 600px;
      margin: 0 auto;
      background-color: #ffffff;
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
      border: 1px solid #e1e4e8;
    }}
    .header {{
      background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
      padding: 30px;
      text-align: center;
    }}
    .header h1 {{
      color: #ffffff;
      margin: 0;
      font-size: 24px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }}
    .content {{
      padding: 40px 30px;
      color: #333333;
      line-height: 1.6;
    }}
    .greeting {{
      font-size: 18px;
      font-weight: 600;
      margin-bottom: 16px;
    }}
    .instruction {{
      font-size: 16px;
      color: #4b5563;
      margin-bottom: 24px;
    }}
    .otp-container {{
      background-color: #f3f4f6;
      border-radius: 8px;
      padding: 20px;
      text-align: center;
      margin: 24px 0;
      border: 1px dashed #d1d5db;
    }}
    .otp-code {{
      font-size: 36px;
      font-weight: 800;
      letter-spacing: 6px;
      color: #4f46e5;
      margin: 0;
    }}
    .expiry {{
      font-size: 13px;
      color: #9ca3af;
      margin-top: 10px;
      text-align: center;
    }}
    .footer {{
      background-color: #fafbfc;
      padding: 20px 30px;
      text-align: center;
      border-top: 1px solid #e1e4e8;
      font-size: 12px;
      color: #9ca3af;
    }}
  </style>
</head>
<body>
  <div class="wrapper">
    <div class="container">
      <div class="header">
        <h1>Findora</h1>
      </div>
      <div class="content">
        <div class="greeting">Hello {name},</div>
        <div class="instruction">{instruction_text}</div>
        <div class="otp-container">
          <div class="otp-code">{otp_code}</div>
          <div class="expiry">This OTP is valid for 10 minutes. Do not share it with anyone.</div>
        </div>
        <div class="instruction" style="font-size: 14px; margin-top: 24px;">
          If you did not request this code, you can safely ignore this email.
        </div>
      </div>
      <div class="footer">
        &copy; 2026 Findora. All rights reserved.
      </div>
    </div>
  </div>
</body>
</html>
"""

    def _send():
        # Read API key inside thread to handle dynamic settings reload
        import os
        from django.conf import settings

        # Try retrieving API key from settings first, then directly from environment variable
        api_key = getattr(settings, 'BREVO_API_KEY', None)
        if not api_key:
            api_key = os.environ.get('BREVO_API_KEY', None)

        # Sanitize API key (remove surrounding quotes or whitespaces that might be added during copy-paste in Render UI)
        if api_key:
            api_key = api_key.strip().strip('"').strip("'")

        if not api_key:
            # Gather safe metadata to help the developer debug the configuration mismatch on Render
            env_keys = list(os.environ.keys())
            matched_keys = [k for k in env_keys if "BREVO" in k or "API" in k or "KEY" in k]
            logger.error(
                "Failed to send OTP email: BREVO_API_KEY is not configured in settings/env. "
                "Detected environment keys with matching patterns: %s. "
                "Please verify that 'BREVO_API_KEY' is added as an Environment Variable in the Render Dashboard.",
                matched_keys
            )
            return

        try:
            from brevo import Brevo
            from brevo.transactional_emails import (
                SendTransacEmailRequestSender,
                SendTransacEmailRequestToItem,
            )

            client = Brevo(api_key=api_key)
            client.transactional_emails.send_transac_email(
                subject=subject,
                sender=SendTransacEmailRequestSender(
                    name="Findora",
                    email="rawatlaxman089@gmail.com",
                ),
                to=[
                    SendTransacEmailRequestToItem(
                        email=recipient,
                        name=name,
                    )
                ],
                html_content=html_body,
                text_content=text_body,
            )
            logger.info("OTP email successfully sent via Brevo API to %s for %s", recipient, purpose)

        except ImportError:
            logger.error(
                "Failed to send OTP email: brevo-python package is not installed. "
                "Run 'pip install brevo-python' and redeploy."
            )
        except Exception as e:
            error_msg = str(e)
            if "unauthorized" in error_msg.lower() or "invalid api key" in error_msg.lower():
                logger.error(
                    "Failed to send OTP email: Brevo API key is invalid or unauthorized. "
                    "Please verify your BREVO_API_KEY in the Render Dashboard."
                )
            elif "sender" in error_msg.lower() and ("not found" in error_msg.lower() or "not allowed" in error_msg.lower()):
                logger.error(
                    "Failed to send OTP email: Sender email is not verified in Brevo. "
                    "Verify 'rawatlaxman089@gmail.com' in your Brevo account under Settings → Senders."
                )
            else:
                logger.error("Failed to send OTP email: Brevo API request failed. Reason: %s", error_msg)
            logger.exception("Exception occurred sending OTP email via Brevo API to %s for %s", recipient, purpose)

    thread = threading.Thread(target=_send, daemon=True)
    thread.start()


def verify_otp(user, otp_code, purpose):
    """
    Validate the supplied OTP against the latest active OTP for this user + purpose.

    Returns:
        (True,  success_message)  on valid OTP
        (False, error_message)    on any failure
    """
    try:
        otp = OTPToken.objects.filter(
            user=user,
            purpose=purpose,
            is_used=False,
        ).latest('created_at')
    except OTPToken.DoesNotExist:
        return False, "No active OTP found. Please request a new one."

    # Check expiry first so the message is accurate
    if timezone.now() >= otp.expires_at:
        return False, "OTP has expired. Please request a new one."

    # Check attempt limit
    if otp.attempt_count >= 5:
        return False, "Too many attempts. Please request a new OTP."

    # Validate the code
    if otp.otp_code != otp_code:
        otp.increment_attempt()
        remaining = max(0, 5 - otp.attempt_count)
        return False, f"Invalid OTP. {remaining} attempt(s) remaining."

    # Mark as used on success
    otp.is_used = True
    otp.save(update_fields=['is_used'])
    return True, "OTP verified successfully."


# ─────────────────────────────────────────────────────────────────────────────
# Item Matching & Association Utilities
# ─────────────────────────────────────────────────────────────────────────────

STOP_WORDS = {
    'lost', 'my', 'the', 'a', 'an', 'found', 'please', 'help',
    'of', 'in', 'at', 'on', 'with', 'and', 'for', 'is', 'item',
    'items', 'to', 'from', 'by', 'this', 'that', 'color', 'coloured'
}


def get_matched_found_items_query_for_owner(owner_user):
    """
    Constructs a Django Q filter to match found items legitimately associated with an Owner
    through the application's actual matching, conversation, claim, and notification workflow.

    Business rules:
    1. Returns found items with explicit direct interactions by this Owner:
       - Active/existing Conversations where owner=owner_user
       - Ownership Claims submitted by claimant=owner_user
       - Notifications delivered to user=owner_user
    2. Does NOT automatically link unrelated found items to every new owner who submits
       an item in the same category or with generic title keywords.
    """
    from .models import Item

    # Direct conversation, claim, or notification association
    direct_assoc_q = (
        Q(conversations__owner=owner_user) |
        Q(claims__claimant=owner_user) |
        Q(notifications__user=owner_user)
    )

    return direct_assoc_q


def is_found_item_matched_for_owner(found_item, owner_user):
    """
    Returns True if the given found item is matched or associated with the given Owner.
    """
    from .models import Item

    if found_item.type != 'found' or found_item.status != 'approved':
        return False

    match_q = get_matched_found_items_query_for_owner(owner_user)
    return Item.objects.filter(pk=found_item.pk, status='approved').filter(match_q).exists()


def get_or_create_matched_conversation(item, request_user):
    """
    Resolves or creates the canonical conversation between an Owner and a Finder
    for a specific item transaction.

    Business rules:
    1. A user cannot initiate a conversation with themselves on their own report.
    2. Identifies owner_user and finder_user based on item type and participant role:
       - If item is 'lost': owner_user = item.user, finder_user = request_user
       - If item is 'found': owner_user = request_user, finder_user = item.user
    3. Lookups prioritize any existing active conversation between (owner_user, finder_user)
       for this specific item.
    4. If no conversation exists for this item, creates exactly ONE new Conversation record.
    """
    from .models import Conversation
    from django.db.models import Q, Count, Max

    if item.user == request_user:
        # If user is the item author, check if an existing conversation exists for this item
        conv = Conversation.objects.filter(item=item).filter(
            Q(owner=request_user) | Q(finder=request_user)
        ).annotate(
            msg_count=Count('messages'),
            last_msg_time=Max('messages__sent_at')
        ).order_by('-msg_count', '-last_msg_time', '-created_at').first()

        if conv:
            return conv, None
        return None, "No conversation started yet for this item."

    if item.type == 'lost':
        owner_user = item.user
        finder_user = request_user
    else:
        if item.parent_item:
            owner_user = item.parent_item.user
            finder_user = item.user
        else:
            owner_user = request_user
            finder_user = item.user

    # 1. Look for existing conversation on this exact item
    conv = Conversation.objects.filter(
        item=item,
        owner=owner_user,
        finder=finder_user
    ).first()

    # 2. If not found on this item, look for a conversation on the counterpart item between the same owner and finder in the matching category
    if not conv:
        counterpart_convs = Conversation.objects.filter(
            owner=owner_user,
            finder=finder_user,
            item__category=item.category
        ).annotate(
            msg_count=Count('messages'),
            last_msg_time=Max('messages__sent_at')
        ).order_by('-msg_count', '-last_msg_time', '-created_at')
        conv = counterpart_convs.first()

    if not conv:
        conv = Conversation.objects.create(
            item=item,
            owner=owner_user,
            finder=finder_user
        )

    return conv, None



