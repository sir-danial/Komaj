from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import Order, OrderItem


@pytest.fixture(autouse=True)
def allow_mock_payments(settings):
    """Tests run with DEBUG=False; opt into the mock gateway explicitly.
    Tests that assert the production fail-closed behavior override this to False."""
    settings.PAYMENTS_ALLOW_MOCK = True
    settings.ZARINPAL_MERCHANT_ID = ""


@pytest.fixture
def variant(db):
    cat = Category.objects.create(name="شیرینی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=p, sku="KOL-1KG", label="جعبه یک کیلویی", weight_grams=1000,
        unit_price=Decimal("180000"), min_order_qty=1, stock_qty=40,
    )


@pytest.fixture
def pending_order(db, variant):
    order = Order.objects.create(
        receiver_name="علی محمدی", phone="09121234567", province="تهران",
        city="تهران", postal_code="1234567890", address_line="آدرس",
        shipping_method="post", shipping_label="پست پیشتاز",
        subtotal=Decimal("360000"), vat_amount=Decimal("32400"),
        shipping_cost=Decimal("45000"), total=Decimal("437400"),
    )
    OrderItem.objects.create(
        order=order, variant=variant, product_name="کلمپه",
        variant_label="جعبه یک کیلویی", unit_label="جعبه",
        quantity=2, unit_price=Decimal("180000"), line_total=Decimal("360000"),
    )
    return order
