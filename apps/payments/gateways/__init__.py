"""Gateway selection (Strategy factory).

Env-driven, Zibal first: a real gateway is used as soon as its merchant id is
set; otherwise the mock gateway keeps the flow working without credentials.
Phase 2 can add a country-based router here (e.g. NOWPayments for non-IR).

``get_gateway()`` picks today's configured provider (for starting a payment).
``get_gateway(name)`` re-creates a specific provider — always use this when
finishing an existing Payment, so a row created by one provider is never
verified against another after a config change.
"""
import logging

from django.conf import settings

from .base import (  # noqa: F401
    CallbackResult,
    InitResponse,
    InquiryResponse,
    PaymentError,
    PaymentGateway,
    TransactionDetails,
    VerifyResponse,
)
from .mock import MockGateway
from .zarinpal import ZarinpalGateway  # noqa: F401
from .zibal import ZibalGateway  # noqa: F401

logger = logging.getLogger(__name__)


def _zibal():
    merchant = getattr(settings, "ZIBAL_MERCHANT", "")
    return ZibalGateway(merchant=merchant) if merchant else None


def _zarinpal():
    merchant_id = getattr(settings, "ZARINPAL_MERCHANT_ID", "")
    if not merchant_id:
        return None
    return ZarinpalGateway(merchant_id=merchant_id, sandbox=settings.ZARINPAL_SANDBOX)


def _mock():
    # Fail CLOSED in production: never silently accept the mock (which approves
    # every payment) just because a merchant id env var is missing.
    if not getattr(settings, "PAYMENTS_ALLOW_MOCK", settings.DEBUG):
        return None
    return MockGateway()


BUILDERS = {"zibal": _zibal, "zarinpal": _zarinpal, "mock": _mock}

# Preference order when no provider is named. Zibal is the primary gateway.
PRIORITY = ["zibal", "zarinpal", "mock"]


def get_gateway(name=None):
    """Return the configured gateway, or the specific one named."""
    if name:
        build = BUILDERS.get(name)
        if not build:
            raise PaymentError(f"درگاه پرداخت ناشناخته: {name}")
        gateway = build()
        if not gateway:
            raise PaymentError(f"درگاه پرداخت «{name}» دیگر پیکربندی نشده است.")
        return gateway

    for candidate in PRIORITY:
        gateway = BUILDERS[candidate]()
        if gateway:
            if candidate == "mock":
                logger.warning(
                    "No payment merchant id configured — using MockGateway "
                    "(dev only, approves every payment)."
                )
            return gateway

    raise PaymentError("درگاه پرداخت پیکربندی نشده است (ZIBAL_MERCHANT تنظیم نشده).")
