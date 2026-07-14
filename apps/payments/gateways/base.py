"""Payment gateway Strategy interface.

A gateway turns an order into a redirect to a payment provider, parses the
provider's callback, then verifies the result. Concrete gateways (Zibal,
Zarinpal, mock, and future NOWPayments for phase 2) implement this so
checkout/verify code never branches on provider.

The four steps mirror the providers' own vocabulary:
  request  -> open a session, get a tracking id
  (redirect the customer, they pay)
  parse_callback -> read the provider's return trip
  verify   -> confirm and finalise; money is only ours once this succeeds
  inquiry  -> ask "what happened?" when no callback ever arrived
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime


class PaymentError(Exception):
    pass


@dataclass
class InitResponse:
    authority: str          # provider reference for this attempt (Zibal: trackId)
    redirect_url: str       # where to send the customer's browser
    raw: dict = field(default_factory=dict)


@dataclass
class CallbackResult:
    """The provider's return trip, normalised across providers."""
    authority: str          # tells us which Payment came back
    success: bool           # the provider's *claim* — never settle on this alone
    card_hash: str = ""     # some providers reveal it here and nowhere else
    raw: dict = field(default_factory=dict)


@dataclass
class TransactionDetails:
    """Everything the provider tells us about a transaction.

    Shared by verify and inquiry because both return the same facts; only the
    result codes differ.
    """
    success: bool = False           # verified/verifiable and amount matches
    paid: bool = False              # money was taken from the customer
    verified: bool = False          # already finalised at the provider
    ref_id: str = ""                # settlement reference (Zibal refNumber)
    card_number: str = ""           # masked, e.g. 62741****44
    card_hash: str = ""
    amount_rial: int | None = None
    paid_at: datetime | None = None
    verified_at: datetime | None = None
    status: int | None = None       # provider status code
    status_label: str = ""          # human-readable, Persian
    code: str = ""                  # provider result code
    message: str = ""
    raw: dict = field(default_factory=dict)


# Verify and inquiry return the same shape; the aliases keep call sites readable.
VerifyResponse = TransactionDetails
InquiryResponse = TransactionDetails


class PaymentGateway(ABC):
    name: str

    @abstractmethod
    def request(self, order, callback_url) -> InitResponse:
        """Open a payment session for ``order``; return where to redirect."""

    @abstractmethod
    def parse_callback(self, params) -> CallbackResult:
        """Read the provider's callback params (a QueryDict/dict)."""

    @abstractmethod
    def verify(self, authority, amount_rial) -> VerifyResponse:
        """Confirm a returned payment. ``amount_rial`` is the expected amount in Rial."""

    def inquiry(self, authority, amount_rial=None) -> InquiryResponse:
        """Ask the provider for the current state of a transaction.

        Used to recover payments whose callback never reached us (customer closed
        the tab, our server was down). Providers that can't do this say so.
        """
        raise PaymentError(f"درگاه {self.name} از استعلام پشتیبانی نمی‌کند.")
