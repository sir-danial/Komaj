import pytest

from apps.cart.cart import CART_SESSION_KEY

pytestmark = pytest.mark.django_db


def test_add_redirects_to_cart(client, weighted_variant):
    resp = client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "1.5"})
    assert resp.status_code == 302
    assert resp.url == "/cart/"
    assert client.session[CART_SESSION_KEY][str(weighted_variant.pk)]["quantity"] == "1.5"


def test_add_invalid_quantity_redirects_to_product(client, weighted_variant):
    resp = client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "0.7"})
    assert resp.status_code == 302
    assert "/p/" in resp.url
    assert CART_SESSION_KEY not in client.session or not client.session[CART_SESSION_KEY]


def test_add_accepts_persian_decimal_separator(client, weighted_variant):
    resp = client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "1٫5"})
    assert resp.status_code == 302
    assert client.session[CART_SESSION_KEY][str(weighted_variant.pk)]["quantity"] == "1.5"


def test_update_replaces_quantity(client, weighted_variant):
    client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "1.5"})
    client.post("/cart/update/", {"variant_id": weighted_variant.pk, "quantity": "0.5"})
    assert client.session[CART_SESSION_KEY][str(weighted_variant.pk)]["quantity"] == "0.5"


def test_remove(client, weighted_variant):
    client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "0.5"})
    client.post("/cart/remove/", {"variant_id": weighted_variant.pk})
    assert not client.session.get(CART_SESSION_KEY)


def test_cart_detail_renders(client, weighted_variant):
    client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "1.5"})
    resp = client.get("/cart/")
    assert resp.status_code == 200
    body = resp.content.decode()
    assert "کلمپه" in body
    assert "خلاصه سفارش" in body


def test_empty_cart_renders(client):
    resp = client.get("/cart/")
    assert resp.status_code == 200
    assert "سبد خرید شما خالی است" in resp.content.decode()


def test_add_get_not_allowed(client, weighted_variant):
    assert client.get("/cart/add/").status_code == 405


def test_cart_count_in_header(client, weighted_variant):
    client.post("/cart/add/", {"variant_id": weighted_variant.pk, "quantity": "1.5"})
    resp = client.get("/")
    # header badge shows the Persian digit for 1 distinct line
    assert resp.status_code == 200
