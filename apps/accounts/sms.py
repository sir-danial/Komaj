"""SMS backend Strategy. Real Kavenegar when KAVENEGAR_API_KEY is set, else a
console/log backend so the OTP flow works in dev without credentials.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)


class ConsoleSMSBackend:
    name = "console"

    def send_otp(self, phone, code):
        logger.warning("[MOCK SMS] OTP for %s is %s", phone, code)
        # Visible in runserver console so devs can complete the flow.
        print(f"\n*** کد تأیید کماج برای {phone}: {code} ***\n")  # noqa: T201
        return True


class KavenegarSMSBackend:
    name = "kavenegar"

    def __init__(self, api_key):
        self.api_key = api_key

    def send_otp(self, phone, code):
        # Uses Kavenegar's OTP "lookup/verify" template endpoint in production.
        # kept import-local so the package is only needed when actually used.
        from kavenegar import KavenegarAPI

        api = KavenegarAPI(self.api_key)
        api.verify_lookup({
            "receptor": phone,
            "token": code,
            "template": getattr(settings, "KAVENEGAR_OTP_TEMPLATE", "komaj-otp"),
        })
        return True


def get_sms_backend():
    api_key = getattr(settings, "KAVENEGAR_API_KEY", "")
    if api_key:
        return KavenegarSMSBackend(api_key)
    logger.warning("KAVENEGAR_API_KEY not set — using ConsoleSMSBackend (OTP printed to console).")
    return ConsoleSMSBackend()
