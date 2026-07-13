from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant


@pytest.fixture
def box_variant(db):
    cat = Category.objects.create(name="شیرینی جعبه‌ای", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=p, sku="KOL-1KG", label="جعبه یک کیلویی", weight_grams=1000,
        unit_price=Decimal("180000"), min_order_qty=1, stock_qty=40,
    )


@pytest.fixture
def valid_checkout_data():
    return {
        "receiver_name": "علی محمدی",
        "phone": "09121234567",
        "email": "ali@example.com",
        "province": "تهران",
        "city": "تهران",
        "postal_code": "1234567890",
        "address_line": "خیابان آزادی، پلاک ۱۰",
        "shipping_method": "post",
        "note": "",
        "accept_terms": "on",
    }
