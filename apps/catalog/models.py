"""Catalog models — categories, products and their orderable variants.

Money convention (project-wide): all monetary fields are stored in **Toman**
as integers (``DecimalField(decimal_places=0)``). Iranians price in Toman and
the front-end ``toman`` filter formats these values directly. Conversion to
Rial (×10) happens only at the payment-gateway boundary (Zarinpal needs IRR).

Quantity convention: every variant is a **fixed package** (box of a fixed
weight, or a jar) and ``quantity`` is always a whole number of packages.
Nothing is sold by fractional weight — a «نیم کیلویی» box is its own variant
with its own price. Customer-facing numbers render in Persian digits.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify

_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
# Persian + Arabic-Indic digits -> ASCII, for parsing user input
_FA_TO_EN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")


def _fa(value):
    """Persian digits for user-facing validation messages."""
    return str(value).translate(_EN_TO_FA)


def parse_quantity(value):
    """Whole-number quantity from user input.

    Accepts Persian/Arabic-Indic digits; rejects fractional or non-numeric
    input with a Persian ``ValidationError``. Returns an ``int``.
    """
    text = str(value).strip().translate(_FA_TO_EN)
    try:
        return int(text)
    except (TypeError, ValueError):
        raise ValidationError("تعداد باید عدد صحیح باشد.")


def _fa_slugify(value):
    """Slugify allowing Persian characters (kept readable in URLs)."""
    return slugify(value, allow_unicode=True)


class Category(models.Model):
    name = models.CharField("نام", max_length=100)
    slug = models.SlugField("اسلاگ", unique=True, allow_unicode=True, max_length=120, blank=True)
    description = models.TextField("توضیحات", blank=True)
    image = models.ImageField("تصویر", upload_to="categories/", blank=True, null=True)
    is_active = models.BooleanField("فعال", default=True)
    sort_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _fa_slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category", kwargs={"slug": self.slug})


class Product(models.Model):
    # DB values are historical; semantics now: WEIGHT = boxed sweets in fixed
    # box sizes (نیم/یک/دو کیلویی), PIECE = jars/containers of a fixed weight.
    WEIGHT = "WEIGHT"
    PIECE = "PIECE"
    SALE_UNIT = [
        (WEIGHT, "جعبه‌ای (وزن ثابت)"),
        (PIECE, "ظرفی (عددی)"),
    ]

    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT, verbose_name="دسته‌بندی"
    )
    name = models.CharField("نام", max_length=200)
    subtitle = models.CharField(
        "زیرعنوان", max_length=100, blank=True,
        help_text="ویژگی فرعی که ریزتر زیر نام می‌آید، مثل «روغن حیوانی»",
    )
    slug = models.SlugField("اسلاگ", unique=True, allow_unicode=True, max_length=220, blank=True)
    description = models.TextField("توضیحات", blank=True)
    origin = models.CharField("خاستگاه", max_length=100, blank=True, help_text="مثل «کرمان»")
    sale_unit = models.CharField("واحد فروش", max_length=10, choices=SALE_UNIT, default=WEIGHT)
    is_active = models.BooleanField("فعال", default=True)
    is_featured = models.BooleanField("منتخب صفحه اصلی", default=False)
    is_fresh = models.BooleanField("تازه پخت", default=False, help_text="نمایش نشان «تازه پخت»")
    created_at = models.DateTimeField("ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("به‌روزرسانی", auto_now=True)

    class Meta:
        verbose_name = "محصول"
        verbose_name_plural = "محصولات"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["is_active", "is_featured"])]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _fa_slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def full_name(self):
        """Unambiguous name for cart lines, order snapshots and SEO — the
        subtitle is display-only hierarchy, not part of the big title."""
        return f"{self.name} — {self.subtitle}" if self.subtitle else self.name

    @property
    def is_boxed(self):
        """Boxed sweet (sold as fixed-weight boxes) vs jar/piece product."""
        return self.sale_unit == self.WEIGHT

    @property
    def primary_image(self):
        img = self.images.first()
        return img.image if img else None

    @property
    def default_variant(self):
        """Cheapest active variant — used for catalog card pricing ("from X")."""
        return self.variants.filter(is_active=True).order_by("unit_price").first()


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField("تصویر", upload_to="products/")
    alt = models.CharField("متن جایگزین", max_length=200, blank=True)
    sort_order = models.PositiveIntegerField("ترتیب", default=0)

    class Meta:
        verbose_name = "تصویر محصول"
        verbose_name_plural = "تصاویر محصول"
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.alt or f"تصویر {self.product.name}"


class ProductVariant(models.Model):
    """The orderable, priced package.

    - Boxed sweet: one variant per fixed box size («جعبه نیم کیلویی»,
      «جعبه یک کیلویی», «جعبه دو کیلویی»), ``unit_price`` = price per box.
    - Jar product: a fixed-weight container (e.g. «ظرف ۴۵۰ گرمی»),
      ``unit_price`` = price per jar.

    Quantity is always a whole number of packages (min 1, step 1).
    """

    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField("کد کالا (SKU)", max_length=64, unique=True)
    label = models.CharField("برچسب", max_length=100, blank=True, help_text="مثل «جعبه نیم کیلویی»")
    weight_grams = models.PositiveIntegerField(
        "وزن (گرم)", null=True, blank=True, help_text="وزن ثابت هر بسته/ظرف"
    )
    unit_price = models.DecimalField(
        "قیمت (تومان)", max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="قیمت هر بسته (جعبه یا ظرف)",
    )
    min_order_qty = models.PositiveIntegerField(
        "حداقل سفارش", default=1, validators=[MinValueValidator(1)],
    )
    stock_qty = models.PositiveIntegerField("موجودی", default=0)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        verbose_name = "نوع محصول"
        verbose_name_plural = "انواع محصول"
        ordering = ["unit_price"]

    def __str__(self):
        base = self.product.name
        return f"{base} — {self.label}" if self.label else base

    @property
    def unit_label(self):
        """Human label for the package ("جعبه" or "عدد")."""
        return "جعبه" if self.product.is_boxed else "عدد"

    @property
    def in_stock(self):
        return self.stock_qty >= self.min_order_qty

    def validate_quantity(self, quantity):
        """Validate an order quantity: a whole number of packages within
        min/stock. Raises ``ValidationError`` (Persian message, Persian digits)
        on violation; returns the quantity as an ``int`` on success.
        """
        qty = parse_quantity(quantity)
        if qty <= 0:
            raise ValidationError("تعداد باید بزرگ‌تر از صفر باشد.")
        if qty < self.min_order_qty:
            raise ValidationError(
                f"حداقل تعداد سفارش {_fa(self.min_order_qty)} {self.unit_label} است."
            )
        if qty > self.stock_qty:
            raise ValidationError("موجودی کافی نیست.")
        return qty

    def line_price(self, quantity):
        """Exact line total (Toman) for a whole-number quantity."""
        return self.unit_price * int(quantity)
