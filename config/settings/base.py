from decimal import Decimal
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["*"]),
    USE_S3_STORAGE=(bool, False),
    ZARINPAL_SANDBOX=(bool, True),
)

env_file = BASE_DIR / ".env"
if env_file.exists():
    environ.Env.read_env(str(env_file))

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    "rest_framework",
    "corsheaders",

    "apps.core",
    "apps.catalog",
    "apps.cart",
    "apps.orders",
    "apps.payments",
    "apps.coupons",
    "apps.accounts",
]

MIDDLEWARE = [
    # first: probes hit the pod IP directly, which must bypass ALLOWED_HOSTS
    "apps.core.middleware.HealthCheckMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.cart.context_processors.cart",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --- Database (env-driven; SQLite default, Postgres via DATABASE_URL in phase 2) ---
_default_sqlite = BASE_DIR / "data" / "db.sqlite3"
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{env('SQLITE_PATH', default=str(_default_sqlite))}",
    )
}

if DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"].update({
        "init_command": (
            "PRAGMA journal_mode=WAL;"
            "PRAGMA synchronous=NORMAL;"
            "PRAGMA foreign_keys=ON;"
            "PRAGMA busy_timeout=5000;"
        ),
        "transaction_mode": "IMMEDIATE",
    })
    DATABASES["default"]["CONN_MAX_AGE"] = 60

# --- Cache (env-driven; DatabaseCache default, Redis via CACHE_URL in phase 2) ---
CACHES = {
    "default": env.cache(
        "CACHE_URL",
        default="dbcache://django_cache",
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Asia/Tehran"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"] if (BASE_DIR / "static").exists() else []

MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", default=str(BASE_DIR / "media")))

# --- Storage (env toggle between local disk and ArvanCloud S3) ---
USE_S3_STORAGE = env("USE_S3_STORAGE")

if USE_S3_STORAGE:
    AWS_S3_ENDPOINT_URL = env("ARVAN_S3_ENDPOINT", default="https://s3.ir-thr-at1.arvanstorage.ir")
    AWS_ACCESS_KEY_ID = env("ARVAN_ACCESS_KEY")
    AWS_SECRET_ACCESS_KEY = env("ARVAN_SECRET_KEY")
    AWS_STORAGE_BUCKET_NAME = env("ARVAN_BUCKET")
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = "public-read"
    AWS_QUERYSTRING_AUTH = False
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGIN_URL = "/login/"

# --- OTP (cache-backed; rate limits guard against brute force) ---
OTP_TTL = env.int("OTP_TTL", default=120)
OTP_RESEND_COOLDOWN = env.int("OTP_RESEND_COOLDOWN", default=60)
OTP_MAX_SENDS_PER_HOUR = env.int("OTP_MAX_SENDS_PER_HOUR", default=5)
OTP_MAX_ATTEMPTS = env.int("OTP_MAX_ATTEMPTS", default=5)

# --- Commerce pricing (all amounts in Toman) ---
# VAT 9% per Iran tax rules (modular so it can change without touching call sites).
VAT_RATE = Decimal(env("VAT_RATE", default="0.09"))

# Shipping methods shown at checkout. Cart page uses SHIPPING_ESTIMATE_KEY for a preview.
SHIPPING_METHODS = [
    {"key": "post", "label": "پست پیشتاز (۲ تا ۴ روز کاری)", "cost": Decimal("45000"),
     "tehran_only": False},
    {"key": "tehran_courier", "label": "پیک تهران (همان روز)", "cost": Decimal("80000"),
     "tehran_only": True},
]
SHIPPING_ESTIMATE_KEY = "post"  # method used for the cart-page estimate

# --- Third-party service credentials ---
# Payment gateway. Zibal is the primary provider: set ZIBAL_MERCHANT and it is
# used automatically. Zibal's shared test merchant is literally "zibal", which
# exercises the real endpoints without owning a gateway yet.
ZIBAL_MERCHANT = env("ZIBAL_MERCHANT", default="")
# Domain registered with Zibal (no scheme), e.g. "komaj.ir". Set this to show
# Zibal's trust badge in the footer; empty = no badge (don't claim a gateway we
# don't have yet).
ZIBAL_TRUST_SITE = env("ZIBAL_TRUST_SITE", default="")
# Sweep for payments whose callback never arrived, every N minutes, on a daemon
# thread in the web container (no Celery in phase 1). On by default so a lost
# callback can't quietly cost a sale. Set to 0 to turn it off — do that if you
# move the sweep to a real cron/CronJob running `manage.py reconcile_payments`.
PAYMENTS_RECONCILE_INTERVAL_MINUTES = env("PAYMENTS_RECONCILE_INTERVAL_MINUTES", default=10)
# The mock gateway approves every payment, so it follows DEBUG unless explicitly
# overridden. prod.py pins it to False by default — with no merchant id and no
# mock, payments fail closed rather than silently "succeeding".
PAYMENTS_ALLOW_MOCK = env.bool("PAYMENTS_ALLOW_MOCK", default=DEBUG)
ZARINPAL_MERCHANT_ID = env("ZARINPAL_MERCHANT_ID", default="")
ZARINPAL_SANDBOX = env("ZARINPAL_SANDBOX")
KAVENEGAR_API_KEY = env("KAVENEGAR_API_KEY", default="")

SENTRY_DSN = env("SENTRY_DSN", default="")
if SENTRY_DSN:
    import sentry_sdk
    sentry_sdk.init(dsn=SENTRY_DSN, traces_sample_rate=0.1)
