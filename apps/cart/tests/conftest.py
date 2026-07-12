from decimal import Decimal

import pytest
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory

from apps.catalog.models import Category, Product, ProductVariant


@pytest.fixture
def weighted_variant(db):
    cat = Category.objects.create(name="شیرینی کیلویی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat, sale_unit=Product.WEIGHT)
    return ProductVariant.objects.create(
        product=p, sku="KOL-KG", is_weighted=True, unit_price=Decimal("180000"),
        min_order_qty=Decimal("0.5"), qty_step=Decimal("0.5"), stock_qty=Decimal("40"),
    )


@pytest.fixture
def piece_variant(db):
    cat = Category.objects.create(name="قوطی‌ها", slug="jars")
    p = Product.objects.create(name="ارده", slug="ardeh", category=cat, sale_unit=Product.PIECE)
    return ProductVariant.objects.create(
        product=p, sku="ARD-600", label="قوطی ۶۰۰ گرمی", is_weighted=False,
        unit_price=Decimal("280000"), min_order_qty=Decimal("1"),
        qty_step=Decimal("1"), stock_qty=Decimal("10"),
    )


@pytest.fixture
def request_with_session():
    def _make():
        req = RequestFactory().get("/")
        SessionMiddleware(lambda r: None).process_request(req)
        req.session.save()
        return req
    return _make
