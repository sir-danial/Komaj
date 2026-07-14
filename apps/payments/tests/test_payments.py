import pytest

from apps.orders.models import Order
from apps.payments.gateways import MockGateway, PaymentError, ZarinpalGateway, ZibalGateway, get_gateway
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db

# The mock bank page mimics Zibal's callback shape.
OK = {"success": "1", "status": "2"}
CANCELLED = {"success": "0", "status": "3"}


def test_get_gateway_defaults_to_mock(settings):
    settings.ZIBAL_MERCHANT = ""  # allow_mock_payments fixture enables mock
    assert isinstance(get_gateway(), MockGateway)


def test_get_gateway_fails_closed_in_production(settings):
    # no merchant id + mock not allowed must NOT silently fall back to the mock
    settings.ZIBAL_MERCHANT = ""
    settings.ZARINPAL_MERCHANT_ID = ""
    settings.PAYMENTS_ALLOW_MOCK = False
    with pytest.raises(PaymentError):
        get_gateway()


def test_mock_gateway_page_404_in_production(client, settings):
    settings.PAYMENTS_ALLOW_MOCK = False
    assert client.get("/payment/mock/anything/").status_code == 404


def test_get_gateway_uses_zibal_when_configured(settings):
    settings.ZIBAL_MERCHANT = "653a8f1b2c3d4e5f60718293"
    assert isinstance(get_gateway(), ZibalGateway)


def test_zibal_wins_over_zarinpal(settings):
    """Zibal is the primary gateway; Zarinpal is only the fallback."""
    settings.ZIBAL_MERCHANT = "653a8f1b2c3d4e5f60718293"
    settings.ZARINPAL_MERCHANT_ID = "00000000-0000-0000-0000-000000000000"
    assert isinstance(get_gateway(), ZibalGateway)


def test_get_gateway_uses_zarinpal_when_configured(settings):
    settings.ZARINPAL_MERCHANT_ID = "00000000-0000-0000-0000-000000000000"
    assert isinstance(get_gateway(), ZarinpalGateway)


def test_get_gateway_by_name_finishes_with_the_original_provider(settings):
    """A payment started on the mock must never be verified against Zibal just
    because Zibal got configured in the meantime."""
    settings.ZIBAL_MERCHANT = "653a8f1b2c3d4e5f60718293"
    assert isinstance(get_gateway("mock"), MockGateway)
    assert isinstance(get_gateway(), ZibalGateway)


def test_amount_rial_conversion(pending_order):
    # 437,400 Toman -> 4,374,000 Rial
    assert pending_order.amount_rial == 4374000


def test_payment_start_redirects_to_mock(client, pending_order):
    resp = client.get(f"/payment/start/{pending_order.token}/")
    assert resp.status_code == 302
    assert "/payment/mock/" in resp.url
    payment = Payment.objects.get(order=pending_order)
    assert payment.authority.startswith("MOCK")
    assert payment.amount == pending_order.total


def test_full_happy_path_mock(client, pending_order, variant):
    # 1. start -> mock bank page
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    # 2. approve at mock bank -> callback
    resp = client.get("/payment/verify/", {"trackId": authority, **OK})
    assert resp.status_code == 302
    assert resp.url == pending_order.get_absolute_url()
    # 3. order paid, payment paid, stock decremented
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == Order.PAID
    assert pending_order.paid_at is not None
    assert Payment.objects.get(order=pending_order).status == Payment.PAID
    assert variant.stock_qty == 38  # 40 - 2


def test_payment_details_are_recorded(client, pending_order):
    """Reference number, card, timestamps and gateway status are kept for support."""
    client.get(f"/payment/start/{pending_order.token}/")
    payment = Payment.objects.get(order=pending_order)
    client.get("/payment/verify/", {"trackId": payment.authority, **OK})

    payment.refresh_from_db()
    assert payment.ref_id                       # شماره پیگیری
    assert payment.card_number == "62741****44"
    assert payment.paid_at is not None
    assert payment.verified_at is not None
    assert payment.gateway_status == 1          # پرداخت شده — تأییدشده
    assert payment.gateway_message


def test_callback_cancelled(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    resp = client.get("/payment/verify/", {"trackId": authority, **CANCELLED})
    assert resp.status_code == 302
    pending_order.refresh_from_db()
    assert pending_order.status == Order.PENDING
    assert Payment.objects.get(order=pending_order).status == Payment.FAILED


def test_double_callback_is_idempotent(client, pending_order, variant):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    client.get("/payment/verify/", {"trackId": authority, **OK})
    # replay the callback (e.g. user refreshes) — stock must NOT drop twice
    client.get("/payment/verify/", {"trackId": authority, **OK})
    variant.refresh_from_db()
    assert variant.stock_qty == 38  # decremented exactly once


def test_late_cancel_callback_cannot_unpay_a_paid_order(client, pending_order):
    """A stray success=0 arriving after settlement must not flip PAID to FAILED."""
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    client.get("/payment/verify/", {"trackId": authority, **OK})
    client.get("/payment/verify/", {"trackId": authority, **CANCELLED})
    assert Payment.objects.get(order=pending_order).status == Payment.PAID


def test_start_already_paid_order_redirects(client, pending_order):
    pending_order.mark_paid()
    resp = client.get(f"/payment/start/{pending_order.token}/")
    assert resp.status_code == 302
    assert resp.url == pending_order.get_absolute_url()


def test_callback_unknown_authority_404(client):
    assert client.get("/payment/verify/", {"trackId": "nope", **OK}).status_code == 404


def test_mock_gateway_page_renders(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    resp = client.get(f"/payment/mock/{authority}/")
    assert resp.status_code == 200
    assert "پرداخت موفق" in resp.content.decode()


def test_confirmation_shows_paid_after_payment(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    client.get("/payment/verify/", {"trackId": authority, **OK})
    resp = client.get(pending_order.get_absolute_url())
    assert "پرداخت موفق بود" in resp.content.decode()


# --- نشان اعتماد زیبال ---

def test_trust_badge_hidden_until_gateway_is_live(client, settings):
    """The badge asserts Zibal handles our payments — it must not show before it does."""
    settings.ZIBAL_TRUST_SITE = ""
    body = client.get("/").content.decode()
    assert "gateway.zibal.ir/trustMe" not in body


def test_trust_badge_links_to_the_registered_domain(client, settings):
    settings.ZIBAL_TRUST_SITE = "komaj.ir"
    body = client.get("/").content.decode()
    assert "https://gateway.zibal.ir/trustMe/komaj.ir" in body
