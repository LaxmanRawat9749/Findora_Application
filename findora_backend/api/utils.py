"""
OTP utility functions for Findora.

Provides helpers for generating, creating, sending, and verifying
one-time passwords used in email verification and password reset flows.
"""

import logging
import secrets
import string
import threading

from django.conf import settings
from django.core.mail import send_mail
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
    Send a formatted OTP email to the user for the given purpose.

    The email is dispatched in a background thread so that slow or
    unreachable SMTP servers do not block the HTTP response.  This
    prevents Django's single-threaded ``runserver`` from queuing
    subsequent requests while waiting for SMTP to complete.
    """
    subjects = {
        'email_verify': 'Findora — Verify Your Email',
        'password_reset': 'Findora — Password Reset OTP',
    }
    bodies = {
        'email_verify': (
            f"Hello {user.first_name or user.username},\n\n"
            f"Your email verification OTP is: {otp_code}\n\n"
            f"This OTP expires in 10 minutes.\n"
            f"Do not share this OTP with anyone.\n\n"
            f"— Findora Team"
        ),
        'password_reset': (
            f"Hello {user.first_name or user.username},\n\n"
            f"Your password reset OTP is: {otp_code}\n\n"
            f"This OTP expires in 10 minutes.\n"
            f"If you did not request this, please ignore this email.\n\n"
            f"— Findora Team"
        ),
    }

    subject = subjects.get(purpose, 'Findora OTP')
    body = bodies.get(purpose, f"Your OTP: {otp_code}")
    recipient = user.email

    def _send():
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=False,
            )
            logger.info("OTP email sent to %s for %s", recipient, purpose)
        except Exception:
            logger.exception("Failed to send OTP email to %s for %s", recipient, purpose)

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
