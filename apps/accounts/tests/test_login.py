import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

pytestmark = pytest.mark.django_db
User = get_user_model()
PHONE = "09121234567"


def test_login_request_sends_otp(client):
    resp = client.post("/login/", {"phone": "09121234567"})
    assert resp.status_code == 302
    assert resp.url == "/login/verify/"
    assert client.session["otp_phone"] == PHONE
    assert cache.get(f"otp:code:{PHONE}") is not None


def test_login_request_invalid_phone(client):
    resp = client.post("/login/", {"phone": "12345"})
    assert resp.status_code == 200
    assert "otp_phone" not in client.session


def test_full_login_flow(client):
    client.post("/login/", {"phone": "09121234567"})
    code = cache.get(f"otp:code:{PHONE}")
    resp = client.post("/login/verify/", {"code": code})
    assert resp.status_code == 302
    assert User.objects.filter(username=PHONE).exists()
    # session now authenticated
    assert client.session.get("_auth_user_id")


def test_verify_wrong_code_no_login(client):
    client.post("/login/", {"phone": "09121234567"})
    resp = client.post("/login/verify/", {"code": "000000"})
    assert resp.status_code == 200
    assert not client.session.get("_auth_user_id")


def test_verify_without_pending_phone_redirects(client):
    assert client.get("/login/verify/").status_code == 302


def test_login_persian_digits(client):
    resp = client.post("/login/", {"phone": "۰۹۱۲۳۴۵۶۷۸۹"})
    assert resp.status_code == 302
    assert client.session["otp_phone"] == "09123456789"  # Persian digits normalized


def test_logout(client):
    client.post("/login/", {"phone": "09121234567"})
    code = cache.get(f"otp:code:{PHONE}")
    client.post("/login/verify/", {"code": code})
    assert client.session.get("_auth_user_id")
    client.post("/logout/")
    assert not client.session.get("_auth_user_id")


def test_login_next_redirect_safe(client):
    client.get("/login/?next=/cart/")
    client.post("/login/", {"phone": "09121234567"})
    code = cache.get(f"otp:code:{PHONE}")
    resp = client.post("/login/verify/", {"code": code})
    assert resp.url == "/cart/"


def test_login_next_rejects_external(client):
    client.get("/login/?next=https://evil.example.com")
    client.post("/login/", {"phone": "09121234567"})
    code = cache.get(f"otp:code:{PHONE}")
    resp = client.post("/login/verify/", {"code": code})
    assert resp.url == "/"  # external next ignored
