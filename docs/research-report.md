# گزارش جامع طراحی فروشگاه آنلاین محصولات بومی (Komaj)

> تاریخ: 2026-04-19 (آخرین به‌روزرسانی: Week 1 انجام شد + Foundation فرانت جلوتر از پلن)
> دامنه: طراحی استک فنی برای فروشگاه آنلاین Django، ایران‌محور، با برنامه توسعه بین‌المللی در فاز ۲.
> **تصمیم فاز ۱ (کمینه‌هزینه):** با انتظار ~۱۰ سفارش/هفته برای ۲-۳ ماه اول، استک روی SQLite + کش دیتابیس + تسک‌های sync چیده شده تا فقط هزینه میزبانی پرداخت شود. ↓ بخش «فاز ۱ Lean» را ببینید.

## خلاصه اجرایی و تصمیم کلیدی

مهم‌ترین یافته: **هیچ‌کدام از Django Oscar و Saleor به‌طور پیش‌فرض quantity اعشاری در سبد خرید پشتیبانی نمی‌کنند** (هر دو از `PositiveIntegerField` استفاده می‌کنند). چون نیاز اصلی فروش کیلویی با گام ۰.۵ (مثل ۱.۵kg شیرینی) است، توصیه قوی **پیاده‌سازی سفارشی با Django + DRF** است، نه fork کردن فریمورک.

---

## ۱. معماری — مقایسه و توصیه

| معیار | Django Oscar | Saleor | Custom (Django+DRF) |
|-------|--------------|--------|---------------------|
| معماری | مونولیت Django | Headless GraphQL + React جدا | کامل در کنترل شما |
| SSR برای SEO | عالی | نیاز به Next.js جدا | عالی |
| **quantity اعشاری** | خیر | خیر | بله |
| وزن محصول | قابل اضافه | فیلد weight native | سفارشی |
| RTL/فارسی | سفارشی‌سازی لازم | فرانت جدا لازم | کامل در کنترل |
| پنل ادمین | Django admin + Dashboard | React Dashboard | Django admin (کافی) |

**توصیه نهایی: Django + DRF سفارشی** — کاتالوگ محدود است (۲ دسته)، Oscar با 20+ اپ داخلی اضافه است، و fork کردن برای quantity اعشاری هزینه نگهداری طولانی‌مدت بالا دارد.

### مدل داده پیشنهادی

```python
# products/models.py
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)

class Product(models.Model):
    SALE_UNIT = [
        ("WEIGHT", "وزنی (کیلوگرم)"),
        ("PIECE",  "واحدی (قوطی)"),
    ]
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    sale_unit = models.CharField(max_length=10, choices=SALE_UNIT)
    is_active = models.BooleanField(default=True)

class ProductVariant(models.Model):
    """
    برای محصول وزنی: یک variant پیش‌فرض با price_per_kg، min_step=0.5
    برای محصول واحدی: چند variant (200g, 600g) هر کدام قیمت ثابت
    """
    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField(max_length=64, unique=True)
    label = models.CharField(max_length=100, blank=True)  # مثل "قوطی 200g"
    weight_grams = models.PositiveIntegerField(null=True, blank=True)  # فقط برای واحدی
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)  # ریال
    is_weighted = models.BooleanField(default=False)
    min_order_qty = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1"))
    qty_step = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("1"))
    stock_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Cart(models.Model):
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.DecimalField(
        max_digits=8, decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))]
    )
    unit_price_snapshot = models.DecimalField(max_digits=12, decimal_places=0)

class Order(models.Model):
    STATUS = [("PENDING","در انتظار پرداخت"), ("PAID","پرداخت شده"),
              ("PACKED","بسته‌بندی"), ("SHIPPED","ارسال شده"),
              ("DELIVERED","تحویل"), ("CANCELED","لغو")]
    code = models.CharField(max_length=16, unique=True)
    user = models.ForeignKey("auth.User", null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=16, choices=STATUS, default="PENDING")
    subtotal = models.DecimalField(max_digits=14, decimal_places=0)
    vat_amount = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    shipping_cost = models.DecimalField(max_digits=14, decimal_places=0, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=0)

class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    gateway = models.CharField(max_length=32)
    amount = models.DecimalField(max_digits=14, decimal_places=0)
    authority = models.CharField(max_length=128, blank=True)
    ref_id = models.CharField(max_length=128, blank=True)
    status = models.CharField(max_length=16, default="PENDING")
    raw_response = models.JSONField(default=dict, blank=True)
```

> قیمت در ایران با `DecimalField(decimal_places=0)` (ریال صحیح) نگهداری شود؛ ضرب در quantity اعشاری با `Decimal` انجام شود تا خطای float حذف شود.

---

## ۲. درگاه پرداخت ایران (تحت شاپرک)

| درگاه | SDK پایتون | بلوغ | توصیه |
|-------|-----------|-----|-------|
| **Zarinpal** | `zarinpal-py-sdk` رسمی + `django-zarinpal` | بالا | primary |
| **IDPay** | wrapper متعدد | خوب | backup |
| **NextPay** / **Zibal** / **PayPing** | غیررسمی | متوسط | جایگزین |
| **بانک ملت / سامان PSP مستقیم** | SOAP قدیمی | سخت | فقط حجم بالا |

**الزام قانونی:** [اینماد](https://enamad.ir) + [ساماندهی](https://samandehi.ir) باید از **هفته ۱ موازی** شروع شود — blocker رسمی برای فعال‌سازی درگاه سطح کسب‌وکار.

### الگوی Strategy (قویاً توصیه‌شده)

```python
# payments/gateways/base.py
from abc import ABC, abstractmethod

class PaymentGateway(ABC):
    name: str

    @abstractmethod
    def request(self, order, callback_url) -> "InitResponse": ...
    @abstractmethod
    def verify(self, authority, amount) -> "VerifyResponse": ...
    @abstractmethod
    def refund(self, ref_id, amount): ...

# payments/gateways/zarinpal.py
import requests

class ZarinpalGateway(PaymentGateway):
    name = "zarinpal"
    BASE = "https://payment.zarinpal.com/pg/v4"

    def __init__(self, merchant_id, sandbox=False):
        self.merchant_id = merchant_id
        self.base = "https://sandbox.zarinpal.com/pg/v4" if sandbox else self.BASE

    def request(self, order, callback_url):
        r = requests.post(f"{self.base}/payment/request.json", json={
            "merchant_id": self.merchant_id,
            "amount": int(order.total),
            "currency": "IRR",
            "description": f"سفارش #{order.code}",
            "callback_url": callback_url,
            "metadata": {"order_id": order.code},
        }, timeout=15)
        data = r.json()["data"]
        return InitResponse(
            authority=data["authority"],
            redirect_url=f"https://payment.zarinpal.com/pg/StartPay/{data['authority']}",
        )

    def verify(self, authority, amount):
        r = requests.post(f"{self.base}/payment/verify.json", json={
            "merchant_id": self.merchant_id,
            "amount": int(amount),
            "authority": authority,
        }, timeout=15)
        ...
```

این باعث می‌شود فاز ۲ (بین‌الملل) بدون دست زدن به کد سفارش اضافه شود.

---

## ۳. پرداخت بین‌الملل (فاز ۲) — واقعیت تحریم

- Stripe / PayPal / Square مستقیم از ایران ممکن نیست.
- گزینه‌های عملی:
  1. **ثبت شرکت خارج** (امارات/ترکیه/استونی) + Stripe/Wise — پایدار اما پیچیده
  2. **NOWPayments (crypto)** — بدون نیاز به شرکت خارجی، فقط کیف پول کریپتو — **انتخاب پیشنهادی فاز ۲**
  3. **CoinGate** — AML/KYC اروپایی سخت‌گیر

### معماری پیشنهادی دو-Driver

```
OrderCheckoutService
  └── PaymentRouter
        ├── if user.country == IR → ZarinpalGateway
        └── else                  → NOWPaymentsGateway
```

---

## ۴. لاجستیک و حمل‌ونقل

### داخل ایران

| سرویس | API | کاربرد |
|-------|-----|--------|
| **پست پیشتاز/سفارشی** | B2B (دسترسی سخت)، کتابخانه‌های جامعه | سراسری، مقرون‌به‌صرفه |
| **تیپاکس** | MyTipax B2B | بین‌شهری سریع |
| **اسنپ‌باکس** | B2B | پیک شهری همان‌روز |
| **الوپیک** | API عمومی‌تر | پیک شهری |

**توصیه MVP:** پست پیشتاز + تیپاکس دستی (محاسبه بر اساس جدول وزن/زون)، API realtime بعداً. فرمول پست از [ghaninia/shipping](https://github.com/ghaninia/shipping) (PHP) به پایتون پورت شود.

### بین‌الملل
- **DHL Express** (MyDHL API) — برای برخی مقاصد محدودیت تحریمی
- **Post EMS** — از طریق شرکت پست
- **Aramex** — منطقه خلیج

---

## ۵. SMS و OTP

| سرویس | SDK پایتون | نکته |
|-------|-----------|------|
| **Kavenegar** | [kavenegar-python](https://github.com/kavenegar/kavenegar-python) رسمی | OTP Lookup (پترن تایید شده، ضد اسپم) |
| **Ghasedak** | wrapper Kavenegar-compatible | ارزان‌تر |
| **SMS.ir** | متعدد | رابط وب خوب |
| **Melipayamak** | SDK رسمی | قدیمی‌ترین |

**توصیه:** Kavenegar + `django-phone-verify` برای مدیریت توکن.

```python
# accounts/otp.py
from kavenegar import KavenegarAPI
def send_otp(phone, code):
    api = KavenegarAPI(settings.KAVENEGAR_API_KEY)
    api.verify_lookup({"receptor": phone, "token": code, "template": "otp-shop"})
```

---

## ۶. استقرار روی Hamravesh

### جریان کار

1. **حساب Hamravesh** + محصول **Darkube** (Kubernetes-based PaaS)
2. سرویس‌های managed از پنل: PostgreSQL، Redis، Object Storage
3. اتصال ریپو Git (GitHub یا HamGit) به عنوان **Repository-Based App**
4. Hamravesh با Dockerfile شما build و deploy می‌کند
5. Celery worker + beat به عنوان اپ‌های جدا با همان image
6. SSL خودکار (Let's Encrypt) + custom domain + auto-deploy on push

### Dockerfile نمونه

```dockerfile
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4"]
```

### پشتیبانی‌ها
- PostgreSQL / MySQL managed
- Redis managed
- Object Storage سازگار با S3
- Load Balancer + SSL خودکار
- Custom domain (DNS CNAME)
- Celery worker/beat به عنوان اپ جدا
- Auto-deploy on git push (Webhook)

templateهای آماده:
- [AliBigdeli/Django-Hamravesh-Docker-Celery-Template](https://github.com/AliBigdeli/Django-Hamravesh-Docker-Celery-Template)
- [AliBigdeli/Django-Hamravesh-Docker-Minio-Template](https://github.com/AliBigdeli/Django-Hamravesh-Docker-Minio-Template)

---

## ۷. زیرساخت‌های جانبی

### فاز ۱ Lean (انتخاب فعلی — ~۱۰ سفارش/هفته، کمینه هزینه)

| نقش | انتخاب فاز ۱ | دلیل |
|-----|--------------|------|
| دیتابیس | **SQLite + WAL** روی PVC هم‌راوش | حذف هزینه Postgres managed؛ در این حجم ترافیک کاملاً کافی |
| کش | **Django `DatabaseCache`** (همون SQLite) | بدون Redis؛ برای rate-limit OTP کافی |
| صف تسک | **هیچ — همه چیز sync** | ۱-۲ سفارش در روز؛ SMS و verify پرداخت داخل request |
| ذخیره مدیا | **ArvanCloud Object Storage پلن رایگان** | جلوگیری از از دست رفتن عکس‌ها در redeploy |
| بک‌آپ DB | **cron شبانه `sqlite3 .backup` + آپلود به ArvanCloud** | ساده و تقریباً رایگان |
| CDN | فعلاً نه (مستقیم از هم‌راوش) | حجم ترافیک نیاز به CDN ندارد |
| ایمیل | SMTP ساده یا حذف (فقط SMS) | هزینه صفر |
| Monitoring | Sentry پلن رایگان | استاندارد |

### ملاحظات عملی فاز ۱

- **PVC روی هم‌راوش الزامی است** — بدون persistent volume، هر redeploy SQLite را پاک می‌کند.
- **تنها ۱ gunicorn worker با چند thread** اجرا شود (`gunicorn --workers 1 --threads 4`) تا:
  - مشکل concurrent writer SQLite کم شود
  - اگر فردا LocMemCache خواستید، بین workerها fragment نشود
- **WAL mode** حتماً فعال: `PRAGMA journal_mode=WAL;` در migration اول.
- کل settings به‌صورت **env-driven** طراحی شود تا فاز ۲ فقط با تغییر env به Postgres/Redis سوییچ شود (بدون تغییر کد).

### جدول ارتقای فاز ۲ (وقتی ترافیک رشد کرد)

| نقش | فاز ۱ → فاز ۲ |
|-----|---------------|
| DB | SQLite → PostgreSQL managed (هم‌راوش) |
| کش | DatabaseCache → Redis |
| صف | sync → Celery + Redis broker |
| Migration | `dumpdata` → `loaddata` یا `pgloader` |
| CDN | — → ArvanCloud CDN |

**نشانه‌های زمان ارتقا:**
- بیش از ۵ سفارش همزمان در دقیقه
- ظاهر شدن «database is locked» در لاگ‌ها
- زمان پاسخ میانگین API بالای ۵۰۰ms
- نیاز به تسک پس‌زمینه طولانی (گزارش‌گیری، export)

### تنظیم Django برای ArvanCloud (بدون تغییر بین فاز ۱/۲)

```python
# settings.py
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_S3_ENDPOINT_URL = "https://s3.ir-thr-at1.arvanstorage.ir"
AWS_ACCESS_KEY_ID = env("ARVAN_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = env("ARVAN_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = env("ARVAN_BUCKET")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"
```

### تنظیم SQLite + DatabaseCache

```python
# settings.py (فاز ۱)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("SQLITE_PATH", default="/data/db.sqlite3"),  # روی PVC
        "OPTIONS": {
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL; PRAGMA foreign_keys=ON;",
            "transaction_mode": "IMMEDIATE",
        },
        "CONN_MAX_AGE": 60,
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}
# سپس: python manage.py createcachetable
```

### تنظیم Django برای ArvanCloud

```python
# settings.py
STORAGES = {
    "default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
AWS_S3_ENDPOINT_URL = "https://s3.ir-thr-at1.arvanstorage.ir"
AWS_ACCESS_KEY_ID = env("ARVAN_ACCESS_KEY")
AWS_SECRET_ACCESS_KEY = env("ARVAN_SECRET_KEY")
AWS_STORAGE_BUCKET_NAME = env("ARVAN_BUCKET")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = "public-read"
```

---

## ۸. SEO و فرانت

### توصیه: SSR با Django Templates (نه SPA)

**مزیت SSR:** SEO از روز اول، سرعت بارگذاری اولیه، زیرساخت یکپارچه در یک repo.

### استک فرانت پیشنهادی

- **Django Templates + Tailwind CSS** با **logical properties** (`ms-*`, `pe-*`) — پلاگین `tailwindcss-rtl` انتخاب نشد چون Tailwind 3.4+ خودش logical properties دارد و وابستگی اضافی لازم نیست.
- **HTMX** برای سبد خرید تعاملی بدون SPA کامل
- **Alpine.js** برای رفتار کوچک سمت کلاینت (اختیاری)
- **Vazirmatn + Lalezar** self-host از طریق `@fontsource-variable/vazirmatn` و `@fontsource/lalezar`
- **Schema.org + Product JSON-LD** در هر صفحه محصول
- **Design system**: جزئیات کامل در [docs/design-system.md](./design-system.md). زنده در `/_styleguide/`.
- **sitemap.xml و robots.txt** با `django.contrib.sitemaps`
- **slug فارسی** با `django-autoslug` + unidecode (اختیاری)

### پنل ادمین

**Django admin** + یکی از:
- **django-unfold** (مدرن‌ترین ۲۰۲۵/۲۰۲۶)
- `django-jazzmin` (محبوب، RTL)
- `persian-djnago-admin`

برای کسب‌وکار این سایز، پنل سفارشی لازم نیست.

---

## ۹. ملاحظات حقوقی ایران

### اینماد
- الزامی برای درگاه پرداخت سطح «کسب‌وکار»
- enamad.ir → ثبت‌نام → احراز هویت → ثبت دامنه → بازرسی → نصب لوگو

### ساماندهی
- [samandehi.ir](https://samandehi.ir) — الزام قانونی، هم‌زمان با اینماد

### مالیات بر ارزش افزوده
- نرخ استاندارد **۹٪** (شیرینی و شکلات مشمول)
- در checkout شفاف: `subtotal + VAT + shipping = total`
- سامانه مؤدیان (intamedia.ir) بعد از رشد — در MVP فاکتور دیجیتال کافی

---

## ۱۰. استک نهایی

### requirements.txt — فاز ۱ (Lean)

```txt
Django==5.1.*
djangorestframework==3.15.*
gunicorn==22.*
whitenoise==6.*
django-environ==0.11.*
django-storages[s3]==1.14.*
boto3==1.35.*
django-phone-verify==2.0.*
kavenegar==1.1.*
zarinpal-py-sdk==1.*
requests==2.32.*
Pillow==11.*
django-jalali==7.*
django-unfold==0.40.*
django-autoslug==1.9.*
django-cors-headers==4.*
django-ratelimit==4.*
sentry-sdk==2.*
pytest-django==4.*
factory-boy==3.*
```

### پکیج‌های فاز ۲ (وقتی Postgres/Redis/Celery اضافه کردید)

```txt
psycopg[binary]==3.2.*
celery==5.4.*
redis==5.1.*
django-celery-beat==2.7.*
django-redis==5.4.*
```

### جدول سرویس‌ها — فاز ۱

| نقش | انتخاب | دلیل |
|-----|--------|------|
| PaaS | Hamravesh / Darkube | تنها هزینه ثابت فاز ۱ |
| DB | **SQLite + WAL روی PVC** | بدون هزینه اضافه |
| کش | **Django DatabaseCache** | بدون Redis |
| Payment IR | **Zarinpal** primary + IDPay backup | بلوغ، SDK پایتون |
| Payment Intl (فاز ۲) | **NOWPayments** | تنها گزینه عملی بدون شرکت خارجی |
| SMS/OTP | **Kavenegar** | SDK رسمی، OTP lookup |
| Storage | **ArvanCloud S3** پلن رایگان | داخل ایران، persistent |
| CDN | فاز ۲ | ترافیک پایین نیازی ندارد |
| Error tracking | Sentry رایگان | استاندارد |
| Analytics | Plausible (self-hosted) یا Google Analytics | سبک |

### نمودار معماری — فاز ۱ (Lean)

```
┌─────────────────────────────────────────────────────────┐
│                    Users (Browser)                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
         ┌────────────────────────────┐
         │  Hamravesh LB + SSL        │
         │  (Let's Encrypt, خودکار)   │
         └──────────────┬─────────────┘
                        │
                        ▼
    ┌──────────────────────────────────────────────┐
    │  Django (gunicorn: 1 worker, 4 threads)      │
    │  ├─ Templates + HTMX + Tailwind RTL          │
    │  ├─ DRF (آماده برای موبایل آینده)            │
    │  └─ Sync everything (no Celery)              │
    └──┬──────────────────────┬────────────────┬──┘
       │                      │                │
       ▼                      ▼                ▼
  ┌──────────┐      ┌──────────────────┐  ┌──────────────┐
  │ SQLite   │      │ ArvanCloud       │  │ External APIs│
  │ (WAL)    │      │ Object Storage   │  │ - Zarinpal   │
  │ on PVC   │      │ (رایگان)         │  │ - Kavenegar  │
  │ ├─ data  │      │ ├─ media         │  │ - eNamad     │
  │ └─ cache │      │ └─ db backups    │  │ - پست (دستی) │
  └────┬─────┘      └──────────────────┘  └──────────────┘
       │
       │ cron شبانه
       ▼
   sqlite3 .backup → آپلود به ArvanCloud
```

### نمودار معماری — فاز ۲ (رشد)

```
   ... همان بالا + اضافه شدن:
   - PostgreSQL managed (به جای SQLite)
   - Redis (کش + broker Celery)
   - Celery worker + beat
   - ArvanCloud CDN جلوی static/media
```

---

## ۱۱. نقشه راه MVP — ۸ هفته

| هفته | کار | وضعیت |
|------|-----|-------|
| ۱ | اسکلت Django + Dockerfile + اولین deploy روی Hamravesh + CI. **موازی: شروع اینماد** | ✅ انجام شد (2026-04-19) — به‌علاوه Foundation فرانت (Phase A/B/C design-system §۸) جلوتر از پلن پیاده شد. |
| ۲ (فعلی) | مدل‌ها (Decimal quantity)، admin با django-unfold، اتصال ArvanCloud Storage | 🟡 در جریان |
| ۳ | کاتالوگ، SEO (sitemap, JSON-LD)، جستجو ساده (Postgres trigram) | ⏳ |
| ۴ | سبد خرید با ولیدیشن min_qty و step، تخمین هزینه پست، VAT ۹٪ | ⏳ |
| ۵ | ثبت‌نام/ورود با OTP موبایل (Kavenegar) + django-phone-verify — **ثبت‌نام اختیاری (checkout مهمان فعال)** | ⏳ |
| ۶ | پرداخت Zarinpal (sandbox → prod)، گرفتن merchant_id پس از اینماد | ⏳ |
| ۷ | محاسبه دقیق پست پیشتاز، SMS اعلان، فاکتور PDF (WeasyPrint) | ⏳ |
| ۸ | Sentry، تست E2E، امنیت (CSRF، rate-limit OTP)، بک‌آپ، soft launch، gate برای `/_styleguide/` | ⏳ |

### افزوده‌های scope (تأیید شده 2026-04-19)
- **checkout مهمان**: `Order.user` nullable + `guest_phone`/`guest_email`. اپ مستقل برای کد تخفیف (`apps/coupons`) با `Coupon` + `CouponRedemption`.
- **بدون wishlist** در MVP.

---

## ۱۲. ریسک‌ها و چالش‌ها

| ریسک | احتمال | اثر | کاهش |
|------|--------|-----|------|
| رد شدن یا تأخیر اینماد | متوسط | بالا | هفته ۱ شروع، مدارک آماده |
| خطای quantity اعشاری در پول | بالا | بالا | همه جا `Decimal`، تست مخصوص ۱.۵kg |
| تفاوت قیمت سبد و پرداخت | متوسط | متوسط | snapshot در `CartItem.unit_price_snapshot` |
| double-verify پرداخت | متوسط | بالا | idempotency با lock روی `payment.authority` |
| ناپایداری Zarinpal | کم-متوسط | متوسط | backup gateway (IDPay) |
| brute-force OTP | بالا | بالا | django-ratelimit + قفل + captcha |
| SEO کند اولیه | بالا | متوسط | JSON-LD + sitemap + محتوای اصیل |
| تغییر قوانین مالیات | متوسط | بالا | ماژولار کردن `tax` service |
| پیچیدگی فاز ۲ بین‌الملل | بالا | متوسط | abstraction لایه پرداخت از هفته ۱ |

---

## منابع

### معماری و فریمورک
- [django-oscar docs](https://docs.oscarcommerce.com/en/latest/)
- [django-oscar basket models source](https://django-oscar.readthedocs.io/en/3.0.2/_modules/oscar/apps/basket/abstract_models.html)
- [Saleor ProductVariant docs](https://docs.saleor.io/docs/3.x/api-reference/products/objects/product-variant)
- [Choose Saleor or Oscar — Django Forum](https://forum.djangoproject.com/t/choose-saleor-or-oscar-for-implement-an-e-commerce/2922)

### پرداخت
- [zarinpal-py-sdk](https://pypi.org/project/zarinpal-py-sdk/)
- [django-zarinpal](https://pypi.org/project/django-zarinpal/)
- [parsisolution/gateway — Iranian Payment Gateways](https://github.com/parsisolution/gateway)
- [NOWPayments](https://nowpayments.io/)
- [CoinGate](https://coingate.com/)

### لاجستیک
- [Tipax](https://tipaxco.com/EN)
- [ghaninia/shipping — Iran post calculator](https://github.com/ghaninia/shipping)
- [sajadspeed/post-price](https://github.com/sajadspeed/post-price)
- [TrackingMore Iran Post API](https://www.trackingmore.com/iran-post-tracking-api)

### SMS
- [kavenegar-python](https://github.com/kavenegar/kavenegar-python)
- [ghasedakapi/ghasedak-kavenegar-python](https://github.com/ghasedakapi/ghasedak-kavenegar-python)
- [django-phone-verify](https://github.com/CuriousLearner/django-phone-verify)

### زیرساخت
- [Hamravesh docs](https://docs.hamravesh.com/)
- [AliBigdeli Django-Hamravesh-Celery template](https://github.com/AliBigdeli/Django-Hamravesh-Docker-Celery-Template)
- [AliBigdeli Django-Hamravesh-Minio template](https://github.com/AliBigdeli/Django-Hamravesh-Docker-Minio-Template)
- [ArvanCloud Object Storage docs](https://docs.arvancloud.ir/en/developer-tools/sdk/object-storage/)
- [Liara Django Object Storage](https://docs.liara.ir/app-deploy/django/object-storage/)
- [django-storages S3](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html)

### حقوقی/مالیاتی
- [enamad.ir](https://enamad.ir)
- [samandehi.ir](https://samandehi.ir)
- [Taxation in Iran — Wikipedia](https://en.wikipedia.org/wiki/Taxation_in_Iran)
- [Iran VAT rate — Trading Economics](https://tradingeconomics.com/iran/sales-tax-rate)

### فرانت/ادمین
- [django-unfold](https://unfoldadmin.com/)
- [mraliarman/persian-djnago-admin](https://github.com/mraliarman/persian-djnago-admin)
- [HTMX](https://htmx.org/)
- [Tailwind CSS Logical Properties](https://tailwindcss.com/docs/padding#using-logical-properties)
- [@fontsource-variable/vazirmatn](https://www.npmjs.com/package/@fontsource-variable/vazirmatn)
