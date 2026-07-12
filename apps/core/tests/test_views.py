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
