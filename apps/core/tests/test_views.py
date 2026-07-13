import pytest
from django.contrib.auth import get_user_model

pytestmark = pytest.mark.django_db
User = get_user_model()


def test_styleguide_404_for_public(client):
    # tests run with DEBUG=False; the QA page must be hidden from public traffic
    assert client.get("/_styleguide/").status_code == 404


def test_styleguide_visible_to_staff(client):
    staff = User.objects.create_user("admin", password="x", is_staff=True)
    client.force_login(staff)
    assert client.get("/_styleguide/").status_code == 200


def test_styleguide_visible_in_debug(client, settings):
    settings.DEBUG = True
    assert client.get("/_styleguide/").status_code == 200


def test_healthz_ok(client):
    resp = client.get("/healthz/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_healthz_bypasses_allowed_hosts(client, settings):
    # kube probes hit the pod by bare IP, which is never in ALLOWED_HOSTS
    settings.ALLOWED_HOSTS = ["komaj.ir"]
    resp = client.get("/healthz/", HTTP_HOST="10.0.110.178:8000")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_media_served_without_s3(client, settings, tmp_path):
    # tests run with DEBUG=False: without S3 the media route must still
    # serve uploads from MEDIA_ROOT (prod serves off the persistent volume)
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "products").mkdir()
    (tmp_path / "products" / "sample.txt").write_bytes(b"img")
    resp = client.get("/media/products/sample.txt")
    assert resp.status_code == 200
    assert b"".join(resp.streaming_content) == b"img"
