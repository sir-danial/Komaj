# Komaj

فروشگاه آنلاین محصولات بومی (شیرینی کیلویی + قوطی‌های مکمل). ساخته‌شده با Django، داکرایز شده برای استقرار مستقیم روی Hamravesh.

**وضعیت:** اسکلت + Foundation فرانت فاز ۱ انجام شد (Tailwind + Vazirmatn + primitiveها + styleguide). در جریان: مدل‌های کاتالوگ/سبد/سفارش. (MVP، ~۱۰ سفارش/هفته، بدون Redis/Postgres/Celery).

برای جزئیات معماری و تصمیمات فنی، [docs/research-report.md](docs/research-report.md) را ببینید.
برای سیستم طراحی UI (پالت، تایپ، Moodboard، پلن فرانت)، [docs/design-system.md](docs/design-system.md) را ببینید.
برای wireframe صفحات کلیدی، [docs/wireframes.md](docs/wireframes.md) را ببینید.

## استک فاز ۱

- Django 5.1 + DRF
- SQLite + WAL روی Persistent Volume
- `DatabaseCache` (بدون Redis)
- بدون Celery — تسک‌ها sync
- WhiteNoise برای استاتیک
- ArvanCloud S3 برای مدیا (قابل فعال‌سازی با `USE_S3_STORAGE=True`)

settings کاملاً env-driven است؛ ارتقا به Postgres/Redis در فاز ۲ فقط با ست کردن `DATABASE_URL` و `CACHE_URL` انجام می‌شود.

## ساختار

```
Komaj/
├── config/               # settings (base/dev/prod)، urls، wsgi، asgi
├── apps/
│   └── core/            # healthz، home، styleguide، templatetag کمکی
├── templates/           # base.html، partials (header/footer)، components
├── static/
│   ├── css/src/         # input.css (Tailwind source)
│   ├── css/dist/        # output.css (build artifact — gitignored)
│   └── img/
├── tailwind.config.js   # tokens پالت + تایپ + shadow + RTL content scan
├── package.json         # Tailwind + Vazirmatn self-host via fontsource
├── data/                # SQLite محلی (gitignore)
├── docs/
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
└── requirements.txt
```

## فرانت (Tailwind + Vazirmatn)

سیستم طراحی و wireframeها در [docs/design-system.md](docs/design-system.md) و [docs/wireframes.md](docs/wireframes.md). tokens رنگ/تایپ/فاصله در `tailwind.config.js`. RTL با logical properties (`ms-*`, `pe-*`). Vazirmatn variable از `@fontsource-variable/vazirmatn` self-host.

### build اولین بار

```sh
npm install
npm run build:css            # تولید static/css/dist/output.css
```

برای dev همزمان با runserver:

```sh
npm run watch:css            # ترمینال ۱
python manage.py runserver   # ترمینال ۲
```

### صفحه‌ها

- `/` — صفحه اصلی (نمونه hero + دسته‌بندی + محصولات نمونه)
- `/_styleguide/` — مرجع بصری tokens و primitiveها (QA داخلی)
- `/healthz/` — health check (JSON)

### فیلترهای template

از `apps.core.templatetags.komaj_extras` (بارگذاری با `{% load komaj_extras %}`):

- `{{ "1234"|fa }}` → `۱۲۳۴` — تبدیل ارقام به فارسی
- `{{ 1800000|toman }}` → `۱٬۸۰۰٬۰۰۰` — قیمت با جداکننده فارسی
- `{{ "0.5"|kg }}` → `۰٫۵` — مقدار کیلوگرم اعشاری

### primitive components

هر کدام در `templates/components/` با `{% include %}` قابل استفاده:

- `button.html`  — variant: primary/secondary/ghost/danger، size: sm/md/lg
- `field.html`   — text/tel/email/number/password با label/helper/error
- `select.html`  — با placeholder و options
- `badge.html`   — tone: sand/pistachio/saffron/pomegranate
- `alert.html`   — success/warning/error/info
- `product_card.html` — کارت محصول با weight badge و قیمت
- `breadcrumb.html`

## اجرای محلی

### گزینه ۱: Docker (توصیه‌شده)

```sh
docker compose up --build
```

سایت روی http://localhost:8000 و health روی http://localhost:8000/healthz/

### گزینه ۲: virtualenv

```sh
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # مقادیر dev کافی‌اند
export SQLITE_PATH=$(pwd)/data/db.sqlite3
mkdir -p data
python manage.py migrate
python manage.py createcachetable
python manage.py createsuperuser
python manage.py runserver
```

## متغیرهای محیطی

همه تنظیمات از env خوانده می‌شود. [.env.example](.env.example) را ببینید. موارد کلیدی:

| متغیر | پیش‌فرض | توضیح |
|-------|---------|-------|
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | در prod روی Hamravesh = `config.settings.prod` |
| `DJANGO_SECRET_KEY` | — | **الزامی در prod** |
| `ALLOWED_HOSTS` | `*` | در prod = `komaj.ir,www.komaj.ir` |
| `SQLITE_PATH` | `BASE_DIR/data/db.sqlite3` | در Hamravesh = `/data/db.sqlite3` (PVC mount) |
| `DATABASE_URL` | — | فاز ۲: `postgres://...` برای سوییچ به Postgres |
| `CACHE_URL` | `dbcache://django_cache` | فاز ۲: `rediscache://host:6379/1` |
| `USE_S3_STORAGE` | `False` | در prod = `True` |
| `ARVAN_ACCESS_KEY` / `ARVAN_SECRET_KEY` / `ARVAN_BUCKET` | — | اعتبارنامه ArvanCloud |
| `ZARINPAL_MERCHANT_ID` | — | بعد از گرفتن اینماد |
| `SENTRY_DSN` | — | اختیاری |

## استقرار روی Hamravesh

1. از پنل Hamravesh/Darkube یک **Repository-Based App** بسازید و به این ریپو متصل کنید.
2. **Persistent Volume** به `/data` متصل کنید (برای SQLite). بدون PVC هر redeploy DB را پاک می‌کند.
3. متغیرهای محیطی بالا را در پنل ست کنید (`DJANGO_SETTINGS_MODULE=config.settings.prod`).
4. پس از اولین deploy، از طریق shell کانتینر:
   ```sh
   python manage.py createsuperuser
   ```
5. Health check endpoint برای Hamravesh: `/healthz/`

auto-deploy on push به `main` از طریق webhook ریپو فعال می‌شود.

## نقشه راه

- **فاز ۱ (در جریان):**
  - ✅ اسکلت Django/Docker، CI، Hamravesh-ready
  - ✅ Foundation فرانت: Tailwind + Vazirmatn/Lalezar، tokens، base layout، primitiveها، styleguide (`/_styleguide/`)
  - ⏳ مدل‌های کاتالوگ (Category, Product با DecimalField برای وزن)
  - ⏳ سبد خرید (session-based) + checkout مهمان
  - ⏳ کد تخفیف (Coupon + CouponRedemption)
  - ⏳ پرداخت Zarinpal، OTP Kavenegar
- **فاز ۲:** Postgres، Redis، Celery، CDN، بین‌الملل (NOWPayments)

پلن هفته‌به‌هفته در [docs/research-report.md §۱۱](docs/research-report.md).
