from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.cart.cart import CART_SESSION_KEY, Cart

pytestmark = pytest.mark.django_db


def test_add_and_iter(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 2)
    items = list(cart)
    assert len(items) == 1
    item = items[0]
    assert item["quantity"] == 2
    assert item["unit_price"] == Decimal("180000")
    assert item["line_total"] == Decimal("360000")


def test_add_accumulates(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 1)
    cart.add(box_variant, 2)
    assert list(cart)[0]["quantity"] == 3


def test_add_replace_sets_absolute(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 3)
    cart.add(box_variant, 1, replace=True)
    assert list(cart)[0]["quantity"] == 1


def test_add_accepts_persian_digits(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, "۲")
    assert list(cart)[0]["quantity"] == 2


def test_add_fractional_quantity_raises(request_with_session, box_variant):
    cart = Cart(request_with_session())
    with pytest.raises(ValidationError, match="عدد صحیح"):
        cart.add(box_variant, "1.5")
    with pytest.raises(ValidationError, match="عدد صحیح"):
        cart.add(box_variant, "۱٫۵")


def test_remove(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 1)
    cart.remove(box_variant.pk)
    assert cart.is_empty


def test_subtotal_and_totals(request_with_session, box_variant, jar_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 1)   # 180,000
    cart.add(jar_variant, 1)   # 280,000
    assert cart.subtotal == Decimal("460000")
    totals = cart.totals()
    assert totals["vat"] == Decimal("41400")       # 9% of 460,000
    assert totals["shipping"] == Decimal("45000")  # estimate (post)
    assert totals["total"] == Decimal("546400")


def test_count_is_distinct_lines(request_with_session, box_variant, jar_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 2)
    cart.add(jar_variant, 2)
    assert cart.count == 2


def test_deleted_variant_skipped(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 1)
    box_variant.delete()
    assert list(cart) == []


def test_inactive_variant_dropped(request_with_session, box_variant):
    cart = Cart(request_with_session())
    cart.add(box_variant, 1)
    box_variant.is_active = False
    box_variant.save()
    # a deactivated product must not remain purchasable
    assert list(cart) == []
    assert cart.subtotal == Decimal("0")


def test_legacy_fractional_session_line_dropped(request_with_session, box_variant):
    # sessions from the per-kilogram era may hold "1.5" — drop, don't crash
    request = request_with_session()
    request.session[CART_SESSION_KEY] = {
        str(box_variant.pk): {"quantity": "1.5", "unit_price": "180000"}
    }
    cart = Cart(request)
    assert list(cart) == []
    assert cart.is_empty
