import pytest


@pytest.fixture(autouse=True)
def locmem_cache(settings):
    """OTP uses the cache; DatabaseCache's table isn't created in the test DB,
    so use an isolated in-memory cache for these tests."""
    settings.CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "otp-tests",
        }
    }
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()
