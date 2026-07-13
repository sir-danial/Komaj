"""Order models for guest-first checkout.

An order can belong to a registered user OR a guest (``user`` nullable +
``guest_*`` fields). Line items snapshot the product/variant name, unit price and
quantity so historical orders stay correct even if the catalog later changes.
Money is in Toman. Access to a guest order is via the unguessable ``token`` (the
human-friendly ``code`` is for display/support only).
"""

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.crypto import get_random_string

PROVINCES = [
    "آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "اصفهان", "البرز", "ایلام",
    "بوشهر", "تهران", "چهارمحال و بختیاری", "خراسان جنوبی", "خراسان رضوی",
    "خراسان شمالی", "خوزستان", "زنجان", "سمنان", "سیستان و بلوچستان", "فارس",
    "قزوین", "قم", "کردستان", "کرمان", "کرمانشاه", "کهگیلویه و بویراحمد",
    "گلستان", "گیلان", "لرستان", "مازندران", "مرکزی", "هرمزگان", "همدان", "یزد",
]
PROVINCE_CHOICES = [(p, p) for p in PROVINCES]


def _gen_token():
    return get_random_string(24)


class Order(models.Model):
    PENDING = "PENDING"
    PAID = "PAID"
    PACKED = "PACKED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELED = "CANCELED"
    STATUS = [
        (PENDING, "در انتظار پرداخت"),
        (PAID, "پرداخت‌شده"),
        (PACKED, "بسته‌بندی"),
        (SHIPPED, "ارسال‌شده"),
        (DELIVERED, "تحویل‌شده"),
        (CANCELED, "لغو‌شده"),
    ]

    code = models.CharField("شماره سفارش", max_length=16, unique=True, blank=True)
    token = models.CharField(max_length=32, unique=True, default=_gen_token, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="orders", verbose_name="کاربر",
    )
    status = models.CharField("وضعیت", max_length=16, choices=STATUS, default=PENDING)

    # Contact (guest or mirrored from user)
    receiver_name = models.CharField("نام گیرنده", max_length=120)
    phone = models.CharField("شماره تماس", max_length=15)
    email = models.EmailField("ایمیل", blank=True)

    # Shipping address
    province = models.CharField("استان", max_length=40, choices=PROVINCE_CHOICES)
    city = models.CharField("شهر", max_length=60)
    postal_code = models.CharField("کد پستی", max_length=10)
    address_line = models.TextField("آدرس کامل")
    note = models.TextField("توضیحات سفارش", blank=True)

    # Shipping method
    shipping_method = models.CharField("روش ارسال", max_length=32, blank=True)
    shipping_label = models.CharField(max_length=120, blank=True)

    # Money (Toman)
    subtotal = models.DecimalField("جمع اقلام", max_digits=14, decimal_places=0, default=0)
    discount = models.DecimalField("تخفیف", max_digits=14, decimal_places=0, default=0)
    vat_amount = models.DecimalField("مالیات", max_digits=14, decimal_places=0, default=0)
    shipping_cost = models.DecimalField("هزینه ارسال", max_digits=14, decimal_places=0, default=0)
    total = models.DecimalField("مبلغ کل", max_digits=14, decimal_places=0, default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "سفارش"
        verbose_name_plural = "سفارش‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"سفارش {self.code}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.code:
            # human-friendly sequential-ish code derived from pk
            Order.objects.filter(pk=self.pk).update(code=str(10000 + self.pk))
            self.code = str(10000 + self.pk)

    def get_absolute_url(self):
        return reverse("orders:confirmation", kwargs={"token": self.token})

    @property
    def is_paid(self):
        return self.status not in (self.PENDING, self.CANCELED)

    @property
    def amount_rial(self):
        """Total in Rial for the payment gateway (Zarinpal expects IRR)."""
        return int(self.total) * 10

    def mark_paid(self):
        from django.utils import timezone
        self.status = self.PAID
        self.paid_at = timezone.now()
        self.save(update_fields=["status", "paid_at", "updated_at"])


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    variant = models.ForeignKey(
        "catalog.ProductVariant", on_delete=models.PROTECT, related_name="order_items"
    )
    # snapshots (survive later catalog edits)
    product_name = models.CharField(max_length=200)
    variant_label = models.CharField(max_length=100, blank=True)
    unit_label = models.CharField(max_length=20)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=0)
    line_total = models.DecimalField(max_digits=14, decimal_places=0)

    class Meta:
        verbose_name = "قلم سفارش"
        verbose_name_plural = "اقلام سفارش"

    def __str__(self):
        return f"{self.product_name} × {self.quantity}"

    @property
    def display_name(self):
        return f"{self.product_name} — {self.variant_label}" if self.variant_label else self.product_name
