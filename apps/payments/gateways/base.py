"""Payment gateway Strategy interface.

A gateway turns an order into a redirect to a payment provider, then verifies the
result on callback. Concrete gateways (Zarinpal, mock, and future NOWPayments for
phase 2) implement this so checkout/verify code never branches on provider.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class InitResponse:
    authority: str          # provider reference for this attempt
    redirect_url: str       # where to send the customer's browser
    raw: dict = field(default_factory=dict)


@dataclass
class VerifyResponse:
    success: bool
    ref_id: str = ""        # provider's settlement reference (RefID)
    code: str = ""
    message: str = ""
    raw: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    name: str

    @abstractmethod
    def request(self, order, callback_url) -> InitResponse:
        """Open a payment session for ``order``; return where to redirect."""

    @abstractmethod
    def verify(self, authority, amount_rial) -> VerifyResponse:
        """Confirm a returned payment. ``amount_rial`` is the expected amount in Rial."""
