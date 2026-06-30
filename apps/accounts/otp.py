"""Cache-backed OTP with rate limiting.

Protections (research-report §12 — OTP brute-force is high-risk):
- code valid for OTP_TTL seconds, single 6-digit code per phone
- resend cooldown (can't spam new codes)
- max sends per hour per phone
- max verify attempts per code, then the code is burned

Uses the configured cache (DatabaseCache in phase 1, Redis in phase 2) — no extra
table needed. SMS delivery goes through the pluggable backend in ``sms.py``.
"""
from django.conf import settings
from django.core.cache import cache
from django.utils.crypto import get_random_string

from .sms import get_sms_backend

OTP_TTL = getattr(settings, "OTP_TTL", 120)
RESEND_COOLDOWN = getattr(settings, "OTP_RESEND_COOLDOWN", 60)
MAX_SENDS_PER_HOUR = getattr(settings, "OTP_MAX_SENDS_PER_HOUR", 5)
MAX_ATTEMPTS = getattr(settings, "OTP_MAX_ATTEMPTS", 5)


class OTPError(Exception):
    """Raised for rate-limit / lockout conditions (message is user-facing Persian)."""


def _k(kind, phone):
    return f"otp:{kind}:{phone}"


def request_otp(phone):
    """Generate, store and send an OTP. Raises OTPError if rate-limited."""
    if cache.get(_k("cooldown", phone)):
        raise OTPError("کد قبلاً ارسال شده؛ کمی صبر کنید و دوباره تلاش کنید.")

    sends_key = _k("sends", phone)
    cache.add(sends_key, 0, 3600)
    if (cache.get(sends_key) or 0) >= MAX_SENDS_PER_HOUR:
        raise OTPError("تعداد درخواست‌ها زیاد است. لطفاً یک ساعت دیگر تلاش کنید.")

    code = get_random_string(6, "0123456789")
    cache.set(_k("code", phone), code, OTP_TTL)
    cache.set(_k("attempts", phone), 0, OTP_TTL)
    cache.set(_k("cooldown", phone), 1, RESEND_COOLDOWN)
    try:
        cache.incr(sends_key)
    except ValueError:
        cache.set(sends_key, 1, 3600)

    get_sms_backend().send_otp(phone, code)
    return code  # returned for tests; never exposed to the client


def verify_otp(phone, code):
    """Return True on a correct, unexpired code. Raises OTPError on lockout."""
    stored = cache.get(_k("code", phone))
    if stored is None:
        raise OTPError("کدی یافت نشد یا منقضی شده است. دوباره درخواست دهید.")

    attempts_key = _k("attempts", phone)
    attempts = (cache.get(attempts_key) or 0) + 1
    cache.set(attempts_key, attempts, OTP_TTL)
    if attempts > MAX_ATTEMPTS:
        _burn(phone)
        raise OTPError("تعداد تلاش‌های نادرست زیاد است. کد باطل شد؛ دوباره درخواست دهید.")

    if str(code).strip() != stored:
        return False

    _burn(phone)  # one-time use
    return True


def _burn(phone):
    cache.delete(_k("code", phone))
    cache.delete(_k("attempts", phone))
