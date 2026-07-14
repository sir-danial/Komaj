"""The mock gateway approves every payment, so how it gets enabled is a security
control, not a preference. These tests pin the contract that .env.example promises.
"""
import importlib

import pytest
from django.conf import settings


def test_allow_mock_is_a_real_setting():
    """It must exist as a setting — not silently fall back to a getattr default.
    (It didn't for a while, which made PAYMENTS_ALLOW_MOCK in .env a no-op.)"""
    assert hasattr(settings, "PAYMENTS_ALLOW_MOCK")


@pytest.mark.parametrize("debug_env", ["True", "False"])
def test_prod_never_enables_mock_from_debug_alone(monkeypatch, debug_env):
    """prod pins mock off even if DEBUG=True leaks into the environment."""
    monkeypatch.setenv("DEBUG", debug_env)
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x")
    monkeypatch.delenv("PAYMENTS_ALLOW_MOCK", raising=False)

    prod = importlib.import_module("config.settings.prod")
    importlib.reload(prod)
    assert prod.PAYMENTS_ALLOW_MOCK is False


def test_prod_allows_mock_only_when_asked_explicitly(monkeypatch):
    monkeypatch.setenv("DEBUG", "False")
    monkeypatch.setenv("DJANGO_SECRET_KEY", "x")
    monkeypatch.setenv("PAYMENTS_ALLOW_MOCK", "True")

    prod = importlib.import_module("config.settings.prod")
    importlib.reload(prod)
    assert prod.PAYMENTS_ALLOW_MOCK is True
