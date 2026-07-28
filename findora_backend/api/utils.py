"""
OTP utility functions for Findora.

Provides helpers for generating, creating, sending, and verifying
one-time passwords used in email verification and password reset flows.
"""

import logging
import secrets
import string
import threading

from django.utils import timezone
import resend

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
    using the Resend email service API.

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
        # Read API key and sender email inside thread to handle dynamic settings reload
        from django.conf import settings
        
        api_key = getattr(settings, 'RESEND_API_KEY', None)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'Findora <onboarding@resend.dev>')

        if not api_key:
            logger.error("Failed to send OTP email to %s: RESEND_API_KEY is not configured in settings/env.", recipient)
            return

        try:
            resend.api_key = api_key
            resend.Emails.send({
                "from": from_email,
                "to": recipient,
                "subject": subject,
                "text": text_body,
                "html": html_body
            })
            logger.info("OTP email successfully sent via Resend API to %s for %s", recipient, purpose)
        except Exception:
            logger.exception("Exception occurred sending OTP email via Resend API to %s for %s", recipient, purpose)

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
