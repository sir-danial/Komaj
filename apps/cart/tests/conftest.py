from decimal import Decimal

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

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
def jar_variant(db):
    cat = Category.objects.create(name="ظرف‌ها", slug="jars")
    p = Product.objects.create(name="ارده", slug="ardeh", category=cat, sale_unit=Product.PIECE)
    return ProductVariant.objects.create(
        product=p, sku="ARD-450", label="ظرف ۴۵۰ گرمی", weight_grams=450,
        unit_price=Decimal("280000"), min_order_qty=1, stock_qty=10,
    )


@pytest.fixture
def request_with_session():
    def _make():
        req = RequestFactory().get("/")
        SessionMiddleware(lambda r: None).process_request(req)
        req.session.save()
        return req
    return _make
