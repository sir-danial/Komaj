import pytest
from django.core.cache import cache

from apps.accounts import otp
from apps.accounts.otp import OTPError, request_otp, verify_otp
from apps.accounts.sms import ConsoleSMSBackend, KavenegarSMSBackend, get_sms_backend

pytestmark = pytest.mark.django_db

PHONE = "09121234567"


def test_request_otp_generates_and_stores():
    code = request_otp(PHONE)
    assert len(code) == 6 and code.isdigit()
    assert cache.get(f"otp:code:{PHONE}") == code


def test_verify_correct_code():
    code = request_otp(PHONE)
    assert verify_otp(PHONE, code) is True
    # one-time use: code burned
    assert cache.get(f"otp:code:{PHONE}") is None


def test_verify_wrong_code():
    request_otp(PHONE)
    assert verify_otp(PHONE, "000000") is False


def test_verify_no_code_raises():
    with pytest.raises(OTPError):
        verify_otp(PHONE, "123456")


def test_lockout_after_max_attempts(settings):
    settings.OTP_MAX_ATTEMPTS = 3
    # reload module constant
    otp.MAX_ATTEMPTS = 3
    request_otp(PHONE)
    for _ in range(3):
        assert verify_otp(PHONE, "000000") is False
    with pytest.raises(OTPError):
        verify_otp(PHONE, "000000")
    otp.MAX_ATTEMPTS = 5  # restore


def test_resend_cooldown():
    request_otp(PHONE)
    with pytest.raises(OTPError, match="صبر"):
        request_otp(PHONE)


def test_hourly_send_limit():
    otp.MAX_SENDS_PER_HOUR = 3
    try:
        for _ in range(3):
            cache.delete(f"otp:cooldown:{PHONE}")  # bypass cooldown to test hourly cap
            request_otp(PHONE)
        cache.delete(f"otp:cooldown:{PHONE}")
        with pytest.raises(OTPError, match="ساعت"):
            request_otp(PHONE)
    finally:
        otp.MAX_SENDS_PER_HOUR = 5


def test_get_sms_backend_console_when_no_key(settings):
    settings.KAVENEGAR_API_KEY = ""
    assert isinstance(get_sms_backend(), ConsoleSMSBackend)


def test_get_sms_backend_kavenegar_when_key(settings):
    settings.KAVENEGAR_API_KEY = "test-key"
    assert isinstance(get_sms_backend(), KavenegarSMSBackend)
