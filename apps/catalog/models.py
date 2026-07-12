"""Catalog models — categories, products and their orderable variants.

Money convention (project-wide): all monetary fields are stored in **Toman**
as integers (``DecimalField(decimal_places=0)``). Iranians price in Toman and
the front-end ``toman`` filter formats these values directly. Conversion to
Rial (×10) happens only at the payment-gateway boundary (Zarinpal needs IRR).

Quantity convention: ``quantity`` is a ``Decimal`` so weight-based products can
be ordered in fractional kilograms (e.g. ``0.5``). Unit (jar) products use whole
numbers. Both go through the same validation (``min_order_qty`` + ``qty_step``).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


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
    WEIGHT = "WEIGHT"
    PIECE = "PIECE"
    SALE_UNIT = [
        (WEIGHT, "وزنی (کیلوگرم)"),
        (PIECE, "واحدی (قوطی/عدد)"),
    ]

    category = models.ForeignKey(
        Category, related_name="products", on_delete=models.PROTECT, verbose_name="دسته‌بندی"
    )
    name = models.CharField("نام", max_length=200)
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
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = _fa_slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product", kwargs={"slug": self.slug})

    @property
    def is_weighted(self):
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
    """The orderable, priced unit.

    - Weighted product: typically a single variant with ``is_weighted=True``,
      ``unit_price`` = price per kilogram, ``min_order_qty``/``qty_step`` in kg
      (e.g. 0.5 / 0.5).
    - Piece product: one or more variants (e.g. «قوطی ۲۰۰ گرمی», «۶۰۰ گرمی»),
      ``unit_price`` = price per piece, qty in whole pieces (min 1, step 1).
    """

    product = models.ForeignKey(Product, related_name="variants", on_delete=models.CASCADE)
    sku = models.CharField("کد کالا (SKU)", max_length=64, unique=True)
    label = models.CharField("برچسب", max_length=100, blank=True, help_text="مثل «قوطی ۲۰۰ گرمی»")
    weight_grams = models.PositiveIntegerField(
        "وزن (گرم)", null=True, blank=True, help_text="فقط برای واحدی — وزن هر عدد"
    )
    unit_price = models.DecimalField(
        "قیمت واحد (تومان)", max_digits=12, decimal_places=0,
        validators=[MinValueValidator(Decimal("0"))],
        help_text="وزنی: قیمت هر کیلوگرم — واحدی: قیمت هر عدد",
    )
    is_weighted = models.BooleanField("وزنی", default=False)
    min_order_qty = models.DecimalField(
        "حداقل سفارش", max_digits=6, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    qty_step = models.DecimalField(
        "گام سفارش", max_digits=6, decimal_places=2, default=Decimal("1"),
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    stock_qty = models.DecimalField("موجودی", max_digits=10, decimal_places=2, default=Decimal("0"))
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
        """Human label for the pricing unit ("کیلوگرم" or "عدد")."""
        return "کیلوگرم" if self.is_weighted else "عدد"

    @property
    def in_stock(self):
        return self.stock_qty >= self.min_order_qty

    def validate_quantity(self, quantity):
        """Validate an order quantity against min/step rules.

        Raises ``ValidationError`` (with a Persian message) on violation.
        Returns the quantity as a ``Decimal`` on success.
        """
        qty = Decimal(str(quantity))
        if qty <= 0:
            raise ValidationError("مقدار باید بزرگ‌تر از صفر باشد.")
        if qty < self.min_order_qty:
            raise ValidationError(
                f"حداقل مقدار سفارش {self.min_order_qty} {self.unit_label} است."
            )
        # quantity must land on the step grid measured from min_order_qty
        remainder = (qty - self.min_order_qty) % self.qty_step
        if remainder != 0:
            raise ValidationError(
                f"مقدار باید مضربی از گام {self.qty_step} {self.unit_label} باشد."
            )
        if qty > self.stock_qty:
            raise ValidationError("موجودی کافی نیست.")
        return qty

    def line_price(self, quantity):
        """Exact line total (Toman) for a quantity — Decimal math, no float error."""
        qty = Decimal(str(quantity))
        # unit_price is integer Toman; quantize the product to whole Toman.
        return (self.unit_price * qty).quantize(Decimal("1"))
