from decimal import Decimal
from urllib.parse import unquote

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import Category, Product, ProductVariant, parse_quantity

pytestmark = pytest.mark.django_db


@pytest.fixture
def box_variant():
    cat = Category.objects.create(name="شیرینی جعبه‌ای")
    product = Product.objects.create(name="کلمپه کرمانی", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=product, sku="KOL-1KG", label="جعبه یک کیلویی", weight_grams=1000,
        unit_price=Decimal("180000"), min_order_qty=1, stock_qty=40,
    )


@pytest.fixture
def jar_variant():
    cat = Category.objects.create(name="ظرف‌ها")
    product = Product.objects.create(name="ارده", category=cat, sale_unit=Product.PIECE)
    return ProductVariant.objects.create(
        product=product, sku="ARD-450", label="ظرف ۴۵۰ گرمی", weight_grams=450,
        unit_price=Decimal("280000"), min_order_qty=1, stock_qty=5,
    )


def test_slug_autogen_persian():
    cat = Category.objects.create(name="شیرینی جعبه‌ای")
    assert cat.slug  # non-empty
    product = Product.objects.create(name="کلمپه کرمانی", category=cat)
    assert product.slug
    # reverse() percent-encodes unicode slugs; compare on the decoded form
    assert unquote(product.get_absolute_url()) == f"/p/{product.slug}/"


def test_is_boxed_property():
    cat = Category.objects.create(name="c")
    assert Product.objects.create(name="w", category=cat, sale_unit=Product.WEIGHT).is_boxed
    assert not Product.objects.create(name="p", category=cat, sale_unit=Product.PIECE).is_boxed


def test_full_name_with_subtitle():
    cat = Category.objects.create(name="c")
    plain = Product.objects.create(name="حلوا زرده اعلا", category=cat)
    oily = Product.objects.create(
        name="حلوا زرده اعلا", slug="halva-heyvani", subtitle="روغن حیوانی", category=cat
    )
    assert plain.full_name == "حلوا زرده اعلا"
    assert oily.full_name == "حلوا زرده اعلا — روغن حیوانی"
    assert str(oily) == "حلوا زرده اعلا — روغن حیوانی"


def test_unit_label(box_variant, jar_variant):
    assert box_variant.unit_label == "جعبه"
    assert jar_variant.unit_label == "عدد"


def test_parse_quantity_accepts_persian_digits():
    assert parse_quantity("۲") == 2
    assert parse_quantity(" ۱۲ ") == 12
    assert parse_quantity("3") == 3
    assert parse_quantity(2) == 2


def test_parse_quantity_rejects_fractions_and_junk():
    for bad in ("1.5", "۱٫۵", "0.5", "abc", "", None):
        with pytest.raises(ValidationError, match="عدد صحیح"):
            parse_quantity(bad)


def test_validate_quantity_valid(box_variant):
    assert box_variant.validate_quantity("2") == 2
    assert box_variant.validate_quantity("۲") == 2
    assert box_variant.validate_quantity(1) == 1


def test_validate_quantity_rejects_fractional(box_variant):
    with pytest.raises(ValidationError, match="عدد صحیح"):
        box_variant.validate_quantity("1.5")
    with pytest.raises(ValidationError, match="عدد صحیح"):
        box_variant.validate_quantity(Decimal("0.5"))


def test_validate_quantity_below_min():
    cat = Category.objects.create(name="c")
    product = Product.objects.create(name="کماج", category=cat, sale_unit=Product.WEIGHT)
    variant = ProductVariant.objects.create(
        product=product, sku="KOM-MIN2", label="جعبه یک کیلویی", weight_grams=1000,
        unit_price=Decimal("250000"), min_order_qty=2, stock_qty=10,
    )
    with pytest.raises(ValidationError, match="حداقل"):
        variant.validate_quantity("1")


def test_validate_quantity_zero_or_negative(box_variant):
    with pytest.raises(ValidationError):
        box_variant.validate_quantity("0")
    with pytest.raises(ValidationError):
        box_variant.validate_quantity("-1")


def test_validate_quantity_over_stock(jar_variant):
    with pytest.raises(ValidationError, match="موجودی"):
        jar_variant.validate_quantity("6")  # stock is 5


def test_line_price_exact(box_variant):
    assert box_variant.line_price(1) == Decimal("180000")
    assert box_variant.line_price(3) == Decimal("540000")


def test_in_stock(box_variant):
    assert box_variant.in_stock is True
    box_variant.stock_qty = 0
    assert box_variant.in_stock is False


def test_default_variant_is_cheapest():
    cat = Category.objects.create(name="ظرف‌ها")
    product = Product.objects.create(name="شکلات", category=cat, sale_unit=Product.PIECE)
    ProductVariant.objects.create(product=product, sku="A", unit_price=Decimal("300000"),
                                  min_order_qty=1, stock_qty=10)
    cheap = ProductVariant.objects.create(product=product, sku="B", unit_price=Decimal("120000"),
                                          min_order_qty=1, stock_qty=10)
    assert product.default_variant == cheap
