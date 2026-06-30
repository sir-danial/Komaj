from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.orders.models import Order, OrderItem


@pytest.fixture
def variant(db):
    cat = Category.objects.create(name="شیرینی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=p, sku="KOL-KG", is_weighted=True, unit_price=Decimal("180000"),
        min_order_qty=Decimal("0.5"), qty_step=Decimal("0.5"), stock_qty=Decimal("40"),
    )


@pytest.fixture
def pending_order(db, variant):
    order = Order.objects.create(
        receiver_name="علی محمدی", phone="09121234567", province="تهران",
        city="تهران", postal_code="1234567890", address_line="آدرس",
        shipping_method="post", shipping_label="پست پیشتاز",
        subtotal=Decimal("270000"), vat_amount=Decimal("24300"),
        shipping_cost=Decimal("45000"), total=Decimal("339300"),
    )
    OrderItem.objects.create(
        order=order, variant=variant, product_name="کلمپه", unit_label="کیلوگرم",
        quantity=Decimal("1.5"), unit_price=Decimal("180000"), line_total=Decimal("270000"),
    )
    return order
