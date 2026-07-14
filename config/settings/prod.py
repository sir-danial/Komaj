from pathlib import Path

from .base import *  # noqa: F401,F403
from .base import env

DEBUG = False

# base.py derives this from DEBUG, which is read from the environment — pin it here
# so a stray DEBUG=True in prod's env can't switch on the gateway that approves
# every payment. Set PAYMENTS_ALLOW_MOCK=True explicitly (e.g. staging) to opt in.
PAYMENTS_ALLOW_MOCK = env.bool("PAYMENTS_ALLOW_MOCK", default=False)

# media lives on the persistent volume (same disk as SQLite) so uploads
# survive redeploys; overridable once ArvanCloud S3 takes over
MEDIA_ROOT = Path(env("MEDIA_ROOT", default="/data/media"))

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.request": {"handlers": ["console"], "level": "WARNING", "propagate": False},
    },
}
