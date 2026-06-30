"""Mock gateway for local/dev use when no real merchant credentials are set.

Redirects to a local page that imitates the bank's StartPay screen, so the full
checkout -> pay -> verify -> confirmation flow is exercisable offline. The real
provider decision lives in get_gateway(); this is never selected once
ZARINPAL_MERCHANT_ID is configured.
"""
from django.urls import reverse
from django.utils.crypto import get_random_string

from .base import InitResponse, PaymentGateway, VerifyResponse


class MockGateway(PaymentGateway):
    name = "mock"

    def request(self, order, callback_url):
        authority = "MOCK" + get_random_string(28)
        # local fake bank page; carries the real callback so it can bounce back
        redirect = reverse("payments:mock", kwargs={"authority": authority})
        return InitResponse(authority=authority, redirect_url=redirect)

    def verify(self, authority, amount_rial):
        # The mock bank page only calls back with Status=OK when "approved";
        # reaching verify means success.
        return VerifyResponse(
            success=True,
            ref_id="MOCK-" + authority[-8:],
            code="100",
            message="پرداخت آزمایشی تأیید شد",
        )
