from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.catalog.models import Category, Product, ProductVariant
from apps.coupons.models import Coupon, CouponRedemption
from apps.coupons.services import validate_coupon
from apps.orders.models import Order

pytestmark = pytest.mark.django_db


@pytest.fixture
def variant():
    cat = Category.objects.create(name="شیرینی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=p, sku="KOL-KG", is_weighted=True, unit_price=Decimal("180000"),
        min_order_qty=Decimal("0.5"), qty_step=Decimal("0.5"), stock_qty=Decimal("40"),
    )


# --- model logic ---
def test_code_uppercased_on_save():
    c = Coupon.objects.create(code="welcome10", discount_type=Coupon.PERCENT, value=10)
    assert c.code == "WELCOME10"


def test_percent_discount():
    c = Coupon(code="P10", discount_type=Coupon.PERCENT, value=Decimal("10"))
    assert c.discount_for(Decimal("390000")) == Decimal("39000")


def test_percent_discount_capped():
    c = Coupon(code="P50", discount_type=Coupon.PERCENT, value=Decimal("50"),
               max_discount=Decimal("50000"))
    assert c.discount_for(Decimal("390000")) == Decimal("50000")


def test_fixed_discount():
    c = Coupon(code="F30", discount_type=Coupon.FIXED, value=Decimal("30000"))
    assert c.discount_for(Decimal("390000")) == Decimal("30000")


def test_fixed_discount_never_exceeds_subtotal():
    c = Coupon(code="BIG", discount_type=Coupon.FIXED, value=Decimal("999999"))
    assert c.discount_for(Decimal("90000")) == Decimal("90000")


def test_min_order_amount_blocks():
    c = Coupon.objects.create(code="MIN", discount_type=Coupon.FIXED, value=10000,
                              min_order_amount=Decimal("500000"))
    assert c.availability_error(Decimal("90000")) is not None


def test_expired_coupon_blocked():
    past = timezone.now() - timezone.timedelta(days=1)
    c = Coupon.objects.create(code="OLD", discount_type=Coupon.PERCENT, value=10, valid_until=past)
    assert c.availability_error(Decimal("90000")) is not None


def test_usage_limit_blocked():
    c = Coupon.objects.create(code="ONCE", discount_type=Coupon.PERCENT, value=10,
                              usage_limit=1, used_count=1)
    assert c.availability_error(Decimal("90000")) is not None


def test_validate_coupon_unknown_code():
    with pytest.raises(ValidationError):
        validate_coupon("NOPE", Decimal("90000"))


# --- end-to-end through cart/checkout ---
def test_apply_coupon_updates_cart_totals(client, variant):
    client.post("/cart/add/", {"variant_id": variant.pk, "quantity": "1"})  # 180,000
    Coupon.objects.create(code="P10", discount_type=Coupon.PERCENT, value=10)
    client.post("/coupon/apply/", {"code": "p10"})
    resp = client.get("/cart/")
    body = resp.content.decode()
    assert "P10" in body
    # discount 18,000 shown
    assert "۱۸٬۰۰۰" in body


def test_coupon_flows_into_order(client, variant):
    client.post("/cart/add/", {"variant_id": variant.pk, "quantity": "1"})  # subtotal 180,000
    Coupon.objects.create(code="F30", discount_type=Coupon.FIXED, value=30000)
    client.post("/coupon/apply/", {"code": "F30"})
    data = {
        "receiver_name": "علی", "phone": "09121234567", "province": "تهران", "city": "تهران",
        "postal_code": "1234567890", "address_line": "آدرس", "shipping_method": "post",
        "accept_terms": "on",
    }
    client.post("/checkout/", data)
    order = Order.objects.get()
    assert order.discount == Decimal("30000")
    # subtotal 180,000 - 30,000 = 150,000; vat 13,500; +45,000 = 208,500
    assert order.vat_amount == Decimal("13500")
    assert order.total == Decimal("208500")
    assert CouponRedemption.objects.filter(order=order).count() == 1
    assert Coupon.objects.get(code="F30").used_count == 1


def test_remove_coupon(client, variant):
    # follow=True so each step's flash message renders+clears (real browser behavior)
    client.post("/cart/add/", {"variant_id": variant.pk, "quantity": "1"})
    Coupon.objects.create(code="P10", discount_type=Coupon.PERCENT, value=10)
    client.post("/coupon/apply/", {"code": "P10"}, follow=True)
    resp = client.post("/coupon/remove/", follow=True)
    assert "P10" not in resp.content.decode()


def test_coupon_dropped_when_below_minimum_after_removal(client, variant):
    # apply coupon needing 200k min while cart is 360k, then drop cart below min
    client.post("/cart/add/", {"variant_id": variant.pk, "quantity": "2"})  # 360,000
    Coupon.objects.create(code="MIN200", discount_type=Coupon.PERCENT, value=10,
                          min_order_amount=Decimal("200000"))
    client.post("/coupon/apply/", {"code": "MIN200"}, follow=True)
    resp = client.post("/cart/update/", {"variant_id": variant.pk, "quantity": "0.5"}, follow=True)  # 90,000
    # coupon silently dropped; code no longer shown
    assert "MIN200" not in resp.content.decode()
