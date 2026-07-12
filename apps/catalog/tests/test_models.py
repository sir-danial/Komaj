from decimal import Decimal
from urllib.parse import unquote

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def weighted_variant():
    cat = Category.objects.create(name="شیرینی کیلویی")
    product = Product.objects.create(name="کلمپه کرمانی", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=product, sku="KOL-KG", is_weighted=True,
        unit_price=Decimal("180000"),
        min_order_qty=Decimal("0.5"), qty_step=Decimal("0.5"),
        stock_qty=Decimal("40"),
    )


@pytest.fixture
def piece_variant():
    cat = Category.objects.create(name="قوطی‌ها")
    product = Product.objects.create(name="ارده", category=cat, sale_unit=Product.PIECE)
    return ProductVariant.objects.create(
        product=product, sku="ARD-600", label="قوطی ۶۰۰ گرمی", is_weighted=False,
        unit_price=Decimal("280000"),
        min_order_qty=Decimal("1"), qty_step=Decimal("1"),
        stock_qty=Decimal("5"),
    )


def test_slug_autogen_persian():
    cat = Category.objects.create(name="شیرینی کیلویی")
    assert cat.slug  # non-empty
    product = Product.objects.create(name="کلمپه کرمانی", category=cat)
    assert product.slug
    # reverse() percent-encodes unicode slugs; compare on the decoded form
    assert unquote(product.get_absolute_url()) == f"/p/{product.slug}/"


def test_is_weighted_property():
    cat = Category.objects.create(name="c")
    assert Product.objects.create(name="w", category=cat, sale_unit=Product.WEIGHT).is_weighted
    assert not Product.objects.create(name="p", category=cat, sale_unit=Product.PIECE).is_weighted


def test_unit_label(weighted_variant, piece_variant):
    assert weighted_variant.unit_label == "کیلوگرم"
    assert piece_variant.unit_label == "عدد"


def test_validate_quantity_valid(weighted_variant):
    assert weighted_variant.validate_quantity("1.5") == Decimal("1.5")
    assert weighted_variant.validate_quantity(Decimal("0.5")) == Decimal("0.5")


def test_validate_quantity_below_min(weighted_variant):
    with pytest.raises(ValidationError, match="حداقل"):
        weighted_variant.validate_quantity("0.25")


def test_validate_quantity_off_step(weighted_variant):
    # 0.7 is >= min(0.5) but not on the 0.5 grid
    with pytest.raises(ValidationError, match="گام"):
        weighted_variant.validate_quantity("0.7")


def test_validate_quantity_zero_or_negative(weighted_variant):
    with pytest.raises(ValidationError):
        weighted_variant.validate_quantity("0")
    with pytest.raises(ValidationError):
        weighted_variant.validate_quantity("-1")


def test_validate_quantity_over_stock(piece_variant):
    with pytest.raises(ValidationError, match="موجودی"):
        piece_variant.validate_quantity("6")  # stock is 5


def test_line_price_decimal_exact(weighted_variant):
    # 0.5 kg * 180000 = 90000 — must be exact, no float drift
    assert weighted_variant.line_price("0.5") == Decimal("90000")
    assert weighted_variant.line_price("1.5") == Decimal("270000")


def test_in_stock(weighted_variant):
    assert weighted_variant.in_stock is True
    weighted_variant.stock_qty = Decimal("0.25")  # below min 0.5
    assert weighted_variant.in_stock is False


def test_default_variant_is_cheapest():
    cat = Category.objects.create(name="قوطی‌ها")
    product = Product.objects.create(name="شکلات", category=cat, sale_unit=Product.PIECE)
    ProductVariant.objects.create(product=product, sku="A", unit_price=Decimal("300000"),
                                  min_order_qty=1, qty_step=1, stock_qty=10)
    cheap = ProductVariant.objects.create(product=product, sku="B", unit_price=Decimal("120000"),
                                          min_order_qty=1, qty_step=1, stock_qty=10)
    assert product.default_variant == cheap
