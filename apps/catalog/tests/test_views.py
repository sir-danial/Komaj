from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    cat = Category.objects.create(name="شیرینی کیلویی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat,
                               sale_unit=Product.WEIGHT, is_active=True, is_featured=True)
    ProductVariant.objects.create(product=p, sku="KOL-KG", is_weighted=True,
                                  unit_price=Decimal("180000"), min_order_qty=Decimal("0.5"),
                                  qty_step=Decimal("0.5"), stock_qty=Decimal("40"))
    return p


def test_product_list_ok(client, product):
    resp = client.get("/products/")
    assert resp.status_code == 200
    assert "کلمپه" in resp.content.decode()


def test_category_page_ok(client, product):
    resp = client.get("/c/sweets/")
    assert resp.status_code == 200
    assert "کلمپه" in resp.content.decode()


def test_category_404_when_inactive(client):
    Category.objects.create(name="مخفی", slug="hidden", is_active=False)
    assert client.get("/c/hidden/").status_code == 404


def test_product_detail_ok(client, product):
    resp = client.get("/p/kolompeh/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "کلمپه" in body
    assert "افزودن به سبد" in body


def test_product_detail_404_when_inactive(client):
    cat = Category.objects.create(name="c", slug="c")
    Product.objects.create(name="مخفی", slug="hidden-p", category=cat, is_active=False)
    assert client.get("/p/hidden-p/").status_code == 404


def test_home_lists_featured(client, product):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "کلمپه" in resp.content.decode()
