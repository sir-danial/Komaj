from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def products():
    sweets = Category.objects.create(name="شیرینی کیلویی", slug="sweets")
    jars = Category.objects.create(name="قوطی‌ها", slug="jars")
    kol = Product.objects.create(name="کلمپه کرمانی", slug="kolompeh", category=sweets,
                                 description="با مغز خرما", origin="کرمان", is_active=True)
    ard = Product.objects.create(name="ارده سنتی", slug="ardeh", category=jars,
                                 description="از کنجد", is_active=True)
    Product.objects.create(name="محصول غیرفعال", slug="inactive", category=sweets, is_active=False)
    for p, price in ((kol, "180000"), (ard, "280000")):
        ProductVariant.objects.create(product=p, sku=f"{p.slug}-v", unit_price=Decimal(price),
                                      min_order_qty=1, stock_qty=10)
    return sweets, jars


def test_search_by_name(client, products):
    body = client.get("/search/", {"q": "کلمپه"}).content.decode()
    assert "کلمپه کرمانی" in body
    assert "ارده" not in body.split("محصولات مرتبط")[0]  # not in results


def test_search_by_description(client, products):
    body = client.get("/search/", {"q": "کنجد"}).content.decode()
    assert "ارده سنتی" in body


def test_search_by_origin(client, products):
    body = client.get("/search/", {"q": "کرمان"}).content.decode()
    assert "کلمپه کرمانی" in body


def test_search_by_category_name(client, products):
    body = client.get("/search/", {"q": "قوطی"}).content.decode()
    assert "ارده سنتی" in body


def test_search_excludes_inactive(client, products):
    body = client.get("/search/", {"q": "غیرفعال"}).content.decode()
    assert "نتیجه‌ای" in body  # "no results" message
    assert "محصول غیرفعال" not in body


def test_search_empty_query_prompts(client, products):
    body = client.get("/search/").content.decode()
    assert "عبارتی وارد کنید" in body


def test_search_no_match_empty_state(client, products):
    body = client.get("/search/", {"q": "زعفرانxyz"}).content.decode()
    assert "چیزی پیدا نشد" in body
