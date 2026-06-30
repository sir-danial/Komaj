from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.cart.cart import Cart

pytestmark = pytest.mark.django_db


def test_add_and_iter(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("1.5"))
    items = list(cart)
    assert len(items) == 1
    item = items[0]
    assert item["quantity"] == Decimal("1.5")
    assert item["unit_price"] == Decimal("180000")
    assert item["line_total"] == Decimal("270000")


def test_add_accumulates(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("0.5"))
    cart.add(weighted_variant, Decimal("1.0"))
    assert list(cart)[0]["quantity"] == Decimal("1.5")


def test_add_replace_sets_absolute(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("1.5"))
    cart.add(weighted_variant, Decimal("0.5"), replace=True)
    assert list(cart)[0]["quantity"] == Decimal("0.5")


def test_add_invalid_quantity_raises(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    with pytest.raises(ValidationError):
        cart.add(weighted_variant, Decimal("0.7"))  # off-step


def test_remove(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("0.5"))
    cart.remove(weighted_variant.pk)
    assert cart.is_empty


def test_subtotal_and_totals(request_with_session, weighted_variant, piece_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("0.5"))  # 90,000
    cart.add(piece_variant, Decimal("1"))        # 280,000
    assert cart.subtotal == Decimal("370000")
    totals = cart.totals()
    assert totals["vat"] == Decimal("33300")     # 9% of 370,000
    assert totals["shipping"] == Decimal("45000")  # estimate (post)
    assert totals["total"] == Decimal("448300")


def test_count_is_distinct_lines(request_with_session, weighted_variant, piece_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("1.5"))
    cart.add(piece_variant, Decimal("2"))
    assert cart.count == 2


def test_deleted_variant_skipped(request_with_session, weighted_variant):
    cart = Cart(request_with_session())
    cart.add(weighted_variant, Decimal("0.5"))
    weighted_variant.delete()
    assert list(cart) == []
