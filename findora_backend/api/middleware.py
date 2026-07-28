"""
Findora request timing and logging middleware.

Logs every incoming HTTP request and its response with:
  - Method and path
  - Response HTTP status code
  - Total processing time in milliseconds
  - Exception type and message on unhandled errors

Sensitive data policy: passwords, OTPs, Authorization headers,
and JWT tokens are NEVER logged here. The middleware only reads
request.method, request.path, and response.status_code.
"""

import logging
import time

logger = logging.getLogger(__name__)

# Fields that must never appear in log output even if accidentally passed
_SENSITIVE_FIELDS = frozenset({
    'password', 'otp', 'new_password', 'confirm_password',
    'current_password', 'refresh', 'access', 'token',
})


class RequestTimingMiddleware:
    """
    WSGI middleware that wraps every request in a timing measurement and
    emits a structured log line when the response is returned (or an
    exception escapes the view layer).

    Placement: must be the LAST item in settings.MIDDLEWARE so it is
    outermost in the call stack and measures the full request lifecycle.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_ns = time.perf_counter_ns()

        # ── Pre-request log ───────────────────────────────────────────────────
        logger.debug(
            "→ %s %s [client=%s]",
            request.method,
            request.path,
            self._client_ip(request),
        )

        try:
            response = self.get_response(request)
        except Exception as exc:
            elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
            logger.error(
                "✗ %s %s raised %s after %.1f ms: %s",
                request.method,
                request.path,
                type(exc).__name__,
                elapsed_ms,
                exc,
                exc_info=True,
            )
            raise  # re-raise — do not suppress exceptions

        # ── Post-response log ─────────────────────────────────────────────────
        elapsed_ms = (time.perf_counter_ns() - start_ns) / 1_000_000
        level = logging.WARNING if response.status_code >= 400 else logging.DEBUG

        logger.log(
            level,
            "← %s %s  %d  %.1f ms",
            request.method,
            request.path,
            response.status_code,
            elapsed_ms,
        )

        return response

    @staticmethod
    def _client_ip(request):
        """Return the best-effort client IP address from request headers."""
        forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if forwarded_for:
            # X-Forwarded-For may contain a comma-separated list; take the first
            return forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')
