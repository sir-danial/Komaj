from decimal import Decimal

import pytest

from apps.orders.models import Order
from apps.payments.gateways import MockGateway, PaymentError, ZarinpalGateway, get_gateway
from apps.payments.models import Payment

pytestmark = pytest.mark.django_db


def test_get_gateway_defaults_to_mock(settings):
    settings.ZARINPAL_MERCHANT_ID = ""  # allow_mock_payments fixture enables mock
    assert isinstance(get_gateway(), MockGateway)


def test_get_gateway_fails_closed_in_production(settings):
    # no merchant id + mock not allowed must NOT silently fall back to the mock
    settings.ZARINPAL_MERCHANT_ID = ""
    settings.PAYMENTS_ALLOW_MOCK = False
    with pytest.raises(PaymentError):
        get_gateway()


def test_mock_gateway_page_404_in_production(client, settings):
    settings.PAYMENTS_ALLOW_MOCK = False
    assert client.get("/payment/mock/anything/").status_code == 404


def test_get_gateway_uses_zarinpal_when_configured(settings):
    settings.ZARINPAL_MERCHANT_ID = "00000000-0000-0000-0000-000000000000"
    assert isinstance(get_gateway(), ZarinpalGateway)


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
    resp = client.get("/payment/verify/", {"Authority": authority, "Status": "OK"})
    assert resp.status_code == 302
    assert resp.url == pending_order.get_absolute_url()
    # 3. order paid, payment paid, stock decremented
    pending_order.refresh_from_db()
    variant.refresh_from_db()
    assert pending_order.status == Order.PAID
    assert pending_order.paid_at is not None
    assert Payment.objects.get(order=pending_order).status == Payment.PAID
    assert variant.stock_qty == 38  # 40 - 2


def test_callback_cancelled(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    resp = client.get("/payment/verify/", {"Authority": authority, "Status": "NOK"})
    assert resp.status_code == 302
    pending_order.refresh_from_db()
    assert pending_order.status == Order.PENDING
    assert Payment.objects.get(order=pending_order).status == Payment.FAILED


def test_double_callback_is_idempotent(client, pending_order, variant):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    client.get("/payment/verify/", {"Authority": authority, "Status": "OK"})
    # replay the callback (e.g. user refreshes) — stock must NOT drop twice
    client.get("/payment/verify/", {"Authority": authority, "Status": "OK"})
    variant.refresh_from_db()
    assert variant.stock_qty == 38  # decremented exactly once


def test_start_already_paid_order_redirects(client, pending_order):
    pending_order.mark_paid()
    resp = client.get(f"/payment/start/{pending_order.token}/")
    assert resp.status_code == 302
    assert resp.url == pending_order.get_absolute_url()


def test_callback_unknown_authority_404(client):
    assert client.get("/payment/verify/", {"Authority": "nope", "Status": "OK"}).status_code == 404


def test_mock_gateway_page_renders(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    resp = client.get(f"/payment/mock/{authority}/")
    assert resp.status_code == 200
    assert "پرداخت موفق" in resp.content.decode()


def test_confirmation_shows_paid_after_payment(client, pending_order):
    client.get(f"/payment/start/{pending_order.token}/")
    authority = Payment.objects.get(order=pending_order).authority
    client.get("/payment/verify/", {"Authority": authority, "Status": "OK"})
    resp = client.get(pending_order.get_absolute_url())
    assert "پرداخت موفق بود" in resp.content.decode()
