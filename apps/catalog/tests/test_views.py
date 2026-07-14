from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    cat = Category.objects.create(name="شیرینی جعبه‌ای", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat,
                               sale_unit=Product.WEIGHT, is_active=True, is_featured=True)
    ProductVariant.objects.create(product=p, sku="KOL-1KG", label="جعبه یک کیلویی",
                                  weight_grams=1000, unit_price=Decimal("180000"),
                                  min_order_qty=1, stock_qty=40)
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


def test_variant_image_follows_the_selected_box(client, db):
    """Picking «جعبه نیم کیلویی» must show that box's art, not the 1kg one."""
    import re
    from apps.catalog.models import Category, Product, ProductImage, ProductVariant
    from django.core.files.uploadedfile import SimpleUploadedFile

    # 1x1 gif — enough for ImageField
    gif = (b"GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00ccc,\x00\x00\x00\x00"
           b"\x01\x00\x01\x00\x00\x02\x02D\x01\x00;")
    cat = Category.objects.create(name="شیرینی جعبه‌ای", slug="sw2")
    p = Product.objects.create(name="شیرمال", slug="shirmal-x", category=cat,
                               sale_unit=Product.WEIGHT)
    half = ProductVariant.objects.create(product=p, sku="X-05", label="جعبه نیم کیلویی",
                                         unit_price=Decimal("130000"), min_order_qty=1,
                                         stock_qty=10)
    one = ProductVariant.objects.create(product=p, sku="X-1", label="جعبه یک کیلویی",
                                        unit_price=Decimal("260000"), min_order_qty=1,
                                        stock_qty=10)
    # gallery order deliberately puts the 1kg image first — the page must still
    # open on the cheapest (pre-selected) variant's art
    ProductImage.objects.create(product=p, variant=one, sort_order=0,
                                image=SimpleUploadedFile("one.gif", gif, "image/gif"))
    ProductImage.objects.create(product=p, variant=half, sort_order=1,
                                image=SimpleUploadedFile("half.gif", gif, "image/gif"))

    body = client.get(p.get_absolute_url()).content.decode()
    main = re.search(r'id="main-image" src="([^"]+)"', body).group(1)
    assert main == half.image.url          # cheapest variant is pre-selected
    assert f'data-image="{one.image.url}"' in body   # switching updates the art
