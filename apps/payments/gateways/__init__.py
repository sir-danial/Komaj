"""Gateway selection (Strategy factory).

Env-driven: a real Zarinpal gateway is used as soon as ZARINPAL_MERCHANT_ID is
set; otherwise the mock gateway keeps the flow working without credentials.
Phase 2 can add a country-based router here (e.g. NOWPayments for non-IR).
"""
import logging

from django.conf import settings

from .base import InitResponse, PaymentGateway, VerifyResponse  # noqa: F401
from .mock import MockGateway
from .zarinpal import PaymentError, ZarinpalGateway  # noqa: F401

logger = logging.getLogger(__name__)


def get_gateway():
    merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "")
    if merchant_id:
        return ZarinpalGateway(merchant_id=merchant_id, sandbox=settings.ZARINPAL_SANDBOX)
    # Fail CLOSED in production: never silently accept the mock (which approves
    # every payment) just because the merchant id env var is missing.
    # Mock is allowed only when explicitly enabled (defaults to DEBUG).
    if not getattr(settings, "PAYMENTS_ALLOW_MOCK", settings.DEBUG):
        raise PaymentError(
            "درگاه پرداخت پیکربندی نشده است (ZARINPAL_MERCHANT_ID تنظیم نشده)."
        )
    logger.warning("ZARINPAL_MERCHANT_ID not set — using MockGateway (dev only, no real payments).")
    return MockGateway()
