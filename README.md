# Komaj

فروشگاه آنلاین محصولات بومی (جعبه‌های شیرینی با اندازه ثابت + ظرف‌های حلوا و معجون). ساخته‌شده با Django، داکرایز شده برای استقرار مستقیم روی Hamravesh.

**وضعیت:** جریان کامل خرید فاز ۱ پیاده و روی Darkube مستقر شد — کاتالوگ (جعبه‌های ثابت نیم/یک/دو کیلویی و ظرف‌های ۴۵۰ گرمی؛ تعداد همیشه عدد صحیح) ← سبد ← checkout مهمان ← پرداخت (Zarinpal + درگاه mock) ← تأیید سفارش، به‌علاوه کد تخفیف، ورود اختیاری با OTP، SEO و جستجو. (MVP، ~۱۰ سفارش/هفته، بدون Redis/Postgres/Celery). باقی‌مانده: محاسبه دقیق پست، فاکتور PDF، SMS اعلان سفارش، تست E2E.

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
- `/healthz/` — health check (JSON). از طریق `HealthCheckMiddleware` قبل از چک `ALLOWED_HOSTS` و ریدایرکت SSL جواب داده می‌شود تا probe کوبرنتیز (که با IP پاد درخواست می‌زند) رد نشود.

### فیلترهای template

از `apps.core.templatetags.komaj_extras` (بارگذاری با `{% load komaj_extras %}`):

- `{{ "1234"|fa }}` → `۱۲۳۴` — تبدیل ارقام به فارسی (تعدادها همیشه عدد صحیح‌اند)
- `{{ 1800000|toman }}` → `۱٬۸۰۰٬۰۰۰` — قیمت با جداکننده فارسی

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
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev` | در prod روی Darkube = `config.settings.prod` |
| `DJANGO_SECRET_KEY` | — | **الزامی در prod** — کلید جدا از dev بسازید |
| `ALLOWED_HOSTS` | `*` | فقط hostname، **بدون scheme** — مثلاً `komaj.darkube.ir` |
| `CSRF_TRUSTED_ORIGINS` | — | **با scheme** — مثلاً `https://komaj.darkube.ir` (الزام Django 4+) |
| `SQLITE_PATH` | `BASE_DIR/data/db.sqlite3` | در Hamravesh = `/data/db.sqlite3` (PVC mount) |
| `DATABASE_URL` | — | فاز ۲: `postgres://...` برای سوییچ به Postgres |
| `CACHE_URL` | `dbcache://django_cache` | فاز ۲: `rediscache://host:6379/1` |
| `USE_S3_STORAGE` | `False` | در prod = `True` |
| `ARVAN_ACCESS_KEY` / `ARVAN_SECRET_KEY` / `ARVAN_BUCKET` | — | اعتبارنامه ArvanCloud |
| `ZIBAL_MERCHANT` | — | **درگاه اصلی.** merchant id از پنل زیبال (بعد از اینماد). مقدار `zibal` = مرچنت تستی خود زیبال |
| `ZARINPAL_MERCHANT_ID` | — | درگاه جایگزین؛ فقط وقتی `ZIBAL_MERCHANT` خالی است استفاده می‌شود |
| `SENTRY_DSN` | — | اختیاری |

## درگاه پرداخت (زیبال)

مستندات: <https://help.zibal.ir/ipg/>

جریان پرداخت دقیقاً چهار مرحله‌ی زیباله:
`request` (باز کردن تراکنش و گرفتن `trackId`) ← `start` (ریدایرکت کاربر به درگاه)
← `callback` ← `verify` (نهایی‌سازی) و در صورت نیاز `inquiry` (استعلام).

**نکته‌ی مهم:** اگر تراکنشِ پرداخت‌شده `verify` نشود، زیبال مبلغ را به کارت مشتری
**برمی‌گرداند**. پس verify صرفاً ثبت دفتری نیست؛ نکردنش یعنی از دست دادن فروش.

### راه‌اندازی

```bash
ZIBAL_MERCHANT=<merchant-id-from-panel>   # در پروداکشن
```

تا وقتی درگاه واقعی ندارید:

- `ZIBAL_MERCHANT=` (خالی) → درگاه **mock** (فقط dev؛ در prod پرداخت fail-closed می‌شود)
- `ZIBAL_MERCHANT=zibal` → **مرچنت تستی زیبال**؛ همان endpointهای واقعی، بدون داشتن درگاه

مبالغ در پروژه به **تومان** ذخیره می‌شوند و در مرز درگاه به **ریال** تبدیل
(`order.amount_rial`). قبل از تسویه، مبلغِ پرداخت‌شده با مبلغ سفارش تطبیق داده می‌شود
و در صورت مغایرت سفارش تسویه **نمی‌شود**.

### استعلام تراکنش‌های بلاتکلیف

اگر کاربر پرداخت کند ولی callback به ما نرسد (بستن تب، قطعی شبکه، ری‌استارت سرور)،
سفارش PENDING می‌ماند در حالی که پول جابه‌جا شده. سه راه برای جبران وجود دارد:

**۱. خودکار (پیش‌فرض).** یک thread پس‌زمینه داخل کانتینر وب هر ۱۰ دقیقه پرداخت‌های
بلاتکلیف را از زیبال استعلام می‌گیرد و سفارش‌های واقعاً پرداخت‌شده را تسویه می‌کند.
نیازی به هیچ تنظیمی نیست؛ با اولین deploy کار می‌کند.

```bash
PAYMENTS_RECONCILE_INTERVAL_MINUTES=10   # پیش‌فرض؛ 0 = خاموش
```

**۲. دستی از CLI** (همان منطق؛ برای cron واقعی یا اجرای موردی):

```bash
python manage.py reconcile_payments              # اجرای sweep
python manage.py reconcile_payments --dry-run    # فقط گزارش، بدون تغییر
```

**۳. از ادمین** — اکشن «استعلام وضعیت از درگاه و تسویه سفارش» روی هر پرداخت.

پرداخت‌های جدیدتر از ۱۵ دقیقه نادیده گرفته می‌شوند (کاربر ممکن است هنوز پای درگاه باشد)
و قدیمی‌تر از ۷۲ ساعت هم بررسی نمی‌شوند. اجرای همزمان بی‌خطر است: `reconcile` روی ردیف
قفل می‌گیرد و هر سفارش دقیقاً یک‌بار تسویه (و موجودی یک‌بار کم) می‌شود.

اطلاعات کامل تراکنش (شماره پیگیری/مرجع، شماره کارت ماسک‌شده، زمان پرداخت و تأیید، کد و
پیام وضعیت درگاه) روی مدل `Payment` ذخیره و در ادمین نمایش داده می‌شود.

> اگر بعداً حجم بالا رفت یا worker‌ها زیاد شدند، `PAYMENTS_RECONCILE_INTERVAL_MINUTES=0`
> بگذارید و همان `reconcile_payments` را به‌عنوان CronJob جدا در Darkube اجرا کنید؛
> بقیه‌ی کد تغییری نمی‌کند.

### نشان اعتماد زیبال

با ست کردن `ZIBAL_TRUST_SITE` (دامنه‌ی ثبت‌شده در زیبال، بدون `https://` — مثلاً
`komaj.ir`) نشان اعتماد در فوتر نمایش داده می‌شود. تا وقتی خالی باشد نمایش داده **نمی‌شود**،
چون این نشان ادعا می‌کند پرداخت‌های ما از زیبال می‌گذرد و نباید قبل از داشتن درگاه نشان داده شود.

## استقرار روی Darkube (Hamravesh)

ریپو روی دو remote نگهداری می‌شود: `origin` (GitHub) و `hamgit`
(<https://hamgit.ir/d.familkhalili/komaj>) که Darkube از آن build می‌گیرد.
بعد از هر merge به `main`، به هر دو push کنید: `git push origin main && git push hamgit main`.

تنظیمات اپ در پنل (مقادیر تست‌شده):

| فیلد | مقدار |
|------|-------|
| ریپو / برنچ | `d.familkhalili/komaj` / `main` |
| پورت سرویس | `8000` (مطابق `EXPOSE` در Dockerfile) |
| دستور اجرایی و ورودی‌ها | **خالی** — `ENTRYPOINT`/`CMD` ایمیج، migrate خودکار + gunicorn را اجرا می‌کند |
| Readiness Probe (HTTP) | `/healthz/` (با اسلش آخر) |
| دیسک | پارتیشن ۱ GiB روی mount path `/data` (برای SQLite) |
| Replica | **۱** — SQLite با چند instance همزمان corrupt می‌شود |

نکات:

- بدون دیسک روی `/data` هر redeploy دیتابیس (سفارش‌ها/کاربرها) را پاک می‌کند.
- متغیرهای محیطی جدول بالا را در تب «متغیرهای محیطی» ست کنید. دو خطای رایج اولین deploy:
  `CSRF_TRUSTED_ORIGINS` بدون `https://` (خطای `4_0.E001` در system check) و
  fail شدن probe به‌خاطر `ALLOWED_HOSTS` (حل‌شده با `HealthCheckMiddleware`).
- پس از اولین deploy، از shell کانتینر: `python manage.py createsuperuser`

## نقشه راه

- **فاز ۱ (در جریان):**
  - ✅ اسکلت Django/Docker، CI، Hamravesh-ready
  - ✅ Foundation فرانت: Tailwind + Vazirmatn/Lalezar، tokens، base layout، primitiveها، styleguide (`/_styleguide/`)
  - ✅ مدل‌های کاتالوگ (Category/Product/ProductVariant با DecimalField برای وزن) + admin + صفحات لیست/جزئیات + seed
  - ✅ سبد خرید (session-based) با ولیدیشن min_qty/step + VAT ۹٪ + تخمین ارسال
  - ✅ checkout مهمان + مدل Order/OrderItem + صفحه تأیید سفارش
  - ✅ کد تخفیف (Coupon + CouponRedemption) درصدی/ثابت
  - ✅ پرداخت زیبال (الگوی Strategy؛ Zarinpal به‌عنوان جایگزین) + درگاه mock برای dev، verify با idempotency، fail-closed در prod، ثبت کامل اطلاعات تراکنش (شماره پیگیری/مرجع، کارت، زمان، وضعیت درگاه) و استعلام خودکار تراکنش‌های بلاتکلیف
  - ✅ ورود اختیاری با OTP موبایل (backend Kavenegar/کنسول) با rate-limit
  - ✅ SEO: `sitemap.xml`، `robots.txt`، JSON-LD (Product/Breadcrumb/Organization/WebSite+SearchAction)، Open Graph + canonical
  - ✅ جستجوی محصولات (`/search/`) + gate کردن `/_styleguide/` (فقط DEBUG یا staff)
  - ✅ استقرار روی Darkube (Hamravesh): دیسک پایدار `/data`، probe `/healthz/`، mirror روی Hamgit
  - ⏳ باقی‌مانده: محاسبه دقیق پست پیشتاز، فاکتور PDF (WeasyPrint)، SMS اعلان سفارش، تست E2E، اتصال ArvanCloud، django-unfold
- **فاز ۲:** Postgres، Redis، Celery، CDN، بین‌الملل (NOWPayments)

اپ‌ها: `catalog`، `cart`، `orders`، `payments`، `coupons`، `accounts`. تست‌ها: `pytest` (۱۱۱ تست). کاتالوگ واقعی (۷ محصول برند + تصاویر): `python manage.py seed_catalog` — idempotent؛ محصولات خارج از لاین‌آپ را غیرفعال می‌کند. اسناد برند در [docs/branding/](docs/branding/).

پلن هفته‌به‌هفته در [docs/research-report.md §۱۱](docs/research-report.md).
