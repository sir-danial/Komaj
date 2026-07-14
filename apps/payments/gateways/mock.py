"""Mock gateway for local/dev use when no real merchant credentials are set.

Redirects to a local page that imitates the bank's StartPay screen, so the full
checkout -> pay -> verify -> confirmation flow is exercisable offline. The real
provider decision lives in get_gateway(); this is never selected once a merchant
id is configured, and it is refused outright in production.
"""
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

from .base import CallbackResult, InitResponse, InquiryResponse, PaymentGateway, VerifyResponse


class MockGateway(PaymentGateway):
    name = "mock"

    def request(self, order, callback_url):
        authority = "MOCK" + get_random_string(28)
        # local fake bank page; carries the real callback so it can bounce back
        redirect = reverse("payments:mock", kwargs={"authority": authority})
        return InitResponse(authority=authority, redirect_url=redirect)

    def parse_callback(self, params):
        """The mock bank page mimics Zibal's callback shape."""
        return CallbackResult(
            authority=str(params.get("trackId", "")),
            success=str(params.get("success", "")) == "1",
            raw=dict(params.items()),
        )

    def verify(self, authority, amount_rial):
        # The mock bank page only calls back with success=1 when "approved";
        # reaching verify means success.
        return VerifyResponse(**self._fake(authority, amount_rial))

    def inquiry(self, authority, amount_rial=None):
        return InquiryResponse(**self._fake(authority, amount_rial))

    @staticmethod
    def _fake(authority, amount_rial):
        now = timezone.now()
        return {
            "success": True,
            "paid": True,
            "verified": True,
            "ref_id": "MOCK-" + authority[-8:],
            "card_number": "62741****44",
            "amount_rial": amount_rial,
            "paid_at": now,
            "verified_at": now,
            "status": 1,
            "status_label": "پرداخت شده — تأییدشده",
            "code": "100",
            "message": "پرداخت آزمایشی تأیید شد",
        }
