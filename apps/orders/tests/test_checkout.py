from decimal import Decimal

import pytest

from apps.orders.models import Order

pytestmark = pytest.mark.django_db


def _add_to_cart(client, variant, qty="1.5"):
    client.post("/cart/add/", {"variant_id": variant.pk, "quantity": qty})


def test_checkout_redirects_when_cart_empty(client):
    resp = client.get("/checkout/")
    assert resp.status_code == 302
    assert resp.url == "/cart/"


def test_checkout_page_renders(client, weighted_variant):
    _add_to_cart(client, weighted_variant)
    resp = client.get("/checkout/")
    assert resp.status_code == 200
    assert "تسویه حساب" in resp.content.decode()


def test_checkout_creates_order_and_redirects_to_payment(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant, "1.5")
    resp = client.post("/checkout/", valid_checkout_data)
    assert resp.status_code == 302
    order = Order.objects.get()
    assert resp.url == f"/payment/start/{order.token}/"
    # totals: 1.5 * 180000 = 270000; vat 24300; post 45000 -> 339300
    assert order.subtotal == Decimal("270000")
    assert order.vat_amount == Decimal("24300")
    assert order.shipping_cost == Decimal("45000")
    assert order.total == Decimal("339300")
    assert order.status == Order.PENDING
    assert order.user is None  # guest
    assert order.items.count() == 1
    assert order.code  # human code assigned


def test_checkout_snapshots_line_item(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant, "0.5")
    client.post("/checkout/", valid_checkout_data)
    item = Order.objects.get().items.get()
    assert item.product_name == "کلمپه"
    assert item.quantity == Decimal("0.5")
    assert item.unit_price == Decimal("180000")
    assert item.line_total == Decimal("90000")


def test_checkout_invalid_phone_rerenders(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant)
    valid_checkout_data["phone"] = "123"
    resp = client.post("/checkout/", valid_checkout_data)
    assert resp.status_code == 200
    assert Order.objects.count() == 0


def test_tehran_courier_rejected_for_other_province(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant)
    valid_checkout_data["province"] = "اصفهان"
    valid_checkout_data["city"] = "اصفهان"
    valid_checkout_data["shipping_method"] = "tehran_courier"
    resp = client.post("/checkout/", valid_checkout_data)
    assert resp.status_code == 302
    assert resp.url == "/cart/"  # rejected with message
    assert Order.objects.count() == 0


def test_terms_required(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant)
    del valid_checkout_data["accept_terms"]
    resp = client.post("/checkout/", valid_checkout_data)
    assert resp.status_code == 200
    assert Order.objects.count() == 0


def test_confirmation_page_by_token(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant)
    client.post("/checkout/", valid_checkout_data)
    order = Order.objects.get()
    resp = client.get(f"/order/{order.token}/")
    assert resp.status_code == 200
    assert order.code in resp.content.decode().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))


def test_confirmation_404_for_bad_token(client):
    assert client.get("/order/nonexistent-token/").status_code == 404


def test_stale_cart_rejected(client, weighted_variant, valid_checkout_data):
    _add_to_cart(client, weighted_variant, "1.5")
    # stock drops below ordered qty after item was in cart
    weighted_variant.stock_qty = Decimal("0.5")
    weighted_variant.save()
    resp = client.post("/checkout/", valid_checkout_data)
    assert resp.status_code == 302
    assert resp.url == "/cart/"
    assert Order.objects.count() == 0
