from decimal import Decimal

import pytest

from apps.catalog.models import Category, Product, ProductVariant
from apps.core.templatetags.komaj_extras import ld_json

pytestmark = pytest.mark.django_db


@pytest.fixture
def product():
    cat = Category.objects.create(name="شیرینی کیلویی", slug="sweets")
    p = Product.objects.create(name="کلمپه", slug="kolompeh", category=cat,
                               sale_unit=Product.WEIGHT, origin="کرمان",
                               description="کلمپه سنتی", is_active=True, is_featured=True)
    ProductVariant.objects.create(product=p, sku="KOL-KG", is_weighted=True,
                                  unit_price=Decimal("180000"), min_order_qty=Decimal("0.5"),
                                  qty_step=Decimal("0.5"), stock_qty=Decimal("40"))
    return p


def test_sitemap_lists_products(client, product):
    resp = client.get("/sitemap.xml")
    assert resp.status_code == 200
    assert "application/xml" in resp["Content-Type"]
    body = resp.content.decode()
    assert "/p/" in body and "/c/sweets/" in body


def test_robots_txt(client):
    resp = client.get("/robots.txt")
    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/plain")
    body = resp.content.decode()
    assert "Sitemap:" in body
    assert "Disallow: /checkout/" in body


def test_product_page_has_jsonld(client, product):
    body = client.get("/p/kolompeh/").content.decode()
    assert '"@type": "Product"' in body
    assert '"@type": "BreadcrumbList"' in body
    assert '"priceCurrency": "IRR"' in body
    assert '"price": "1800000"' in body  # 180,000 toman -> rial
    assert '"availability": "https://schema.org/InStock"' in body


def test_product_jsonld_has_root_url(client, product):
    body = client.get("/p/kolompeh/").content.decode()
    # Product schema should carry a root-level url (not only inside Offer)
    assert '"@type": "Product", "name": "کلمپه", "url": "http://testserver/p/' in body


def test_breadcrumb_every_item_has_url(client, product):
    import json
    import re
    body = client.get("/p/kolompeh/").content.decode()
    block = re.search(r'"@type": "BreadcrumbList".*?itemListElement": (\[.*?\])\}', body).group(1)
    items = json.loads(block)
    assert len(items) == 3
    # including the current-page (last) item, every ListItem carries an absolute item URL
    assert all("item" in it and it["item"].startswith("http") for it in items)


def test_search_page_has_breadcrumb_jsonld(client, product):
    body = client.get("/search/", {"q": "کلمپه"}).content.decode()
    assert '"@type": "BreadcrumbList"' in body


def test_product_page_has_og_tags(client, product):
    body = client.get("/p/kolompeh/").content.decode()
    assert '<meta property="og:type" content="product">' in body
    assert 'og:title' in body


def test_home_has_website_searchaction(client, product):
    body = client.get("/").content.decode()
    assert '"@type": "WebSite"' in body
    assert '"@type": "SearchAction"' in body


def test_ld_json_escapes_script_break_out():
    # admin-authored text with a </script> must not break out of the ld+json block
    out = str(ld_json({"name": "</script><script>alert(1)"}))
    assert out.startswith('<script type="application/ld+json">')
    assert out.endswith("</script>")
    # the payload's angle brackets are unicode-escaped, so no raw tag survives
    assert "<script>alert(1)" not in out
    assert "\\u003c" in out and "\\u003e" in out


def test_canonical_has_no_query_string(client, product):
    body = client.get("/search/?q=xyz").content.decode()
    assert '<link rel="canonical" href="http://testserver/search/">' in body
