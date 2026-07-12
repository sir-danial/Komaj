"""Discount coupons (confirmed in scope for MVP).

A coupon is either a percentage (optionally capped by ``max_discount``) or a fixed
Toman amount, with an optional minimum order, validity window and usage limit.
``CouponRedemption`` records each use against an order.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    TYPES = [(PERCENT, "درصدی"), (FIXED, "مبلغ ثابت (تومان)")]

    code = models.CharField("کد", max_length=32, unique=True)
    discount_type = models.CharField("نوع", max_length=10, choices=TYPES, default=PERCENT)
    value = models.DecimalField("مقدار", max_digits=12, decimal_places=0,
                                help_text="درصدی: ۰ تا ۱۰۰ — مبلغ ثابت: تومان")
    max_discount = models.DecimalField("سقف تخفیف (تومان)", max_digits=12, decimal_places=0,
                                       null=True, blank=True, help_text="فقط برای نوع درصدی")
    min_order_amount = models.DecimalField("حداقل مبلغ سفارش", max_digits=14, decimal_places=0, default=0)
    valid_from = models.DateTimeField("از تاریخ", null=True, blank=True)
    valid_until = models.DateTimeField("تا تاریخ", null=True, blank=True)
    usage_limit = models.PositiveIntegerField("سقف دفعات استفاده", null=True, blank=True)
    used_count = models.PositiveIntegerField("دفعات استفاده‌شده", default=0)
    is_active = models.BooleanField("فعال", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کد تخفیف"
        verbose_name_plural = "کدهای تخفیف"
        ordering = ["-created_at"]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def availability_error(self, subtotal):
        """Return a Persian error string if the coupon can't be used, else None."""
        now = timezone.now()
        if not self.is_active:
            return "این کد تخفیف فعال نیست."
        if self.valid_from and now < self.valid_from:
            return "این کد تخفیف هنوز فعال نشده است."
        if self.valid_until and now > self.valid_until:
            return "این کد تخفیف منقضی شده است."
        if self.usage_limit is not None and self.used_count >= self.usage_limit:
            return "ظرفیت استفاده از این کد تخفیف تمام شده است."
        if Decimal(subtotal) < self.min_order_amount:
            return f"حداقل مبلغ سفارش برای این کد {int(self.min_order_amount):,} تومان است."
        return None

    def discount_for(self, subtotal):
        """Discount amount (Toman) for a given subtotal — never exceeds subtotal."""
        subtotal = Decimal(subtotal)
        if self.discount_type == self.PERCENT:
            amount = (subtotal * self.value / Decimal("100")).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP)
            if self.max_discount is not None:
                amount = min(amount, self.max_discount)
        else:
            amount = self.value
        return min(amount, subtotal)


class CouponRedemption(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name="redemptions")
    order = models.ForeignKey("orders.Order", on_delete=models.CASCADE, related_name="redemptions")
    amount = models.DecimalField("مبلغ تخفیف", max_digits=14, decimal_places=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "استفاده از کد تخفیف"
        verbose_name_plural = "استفاده‌های کد تخفیف"

    def __str__(self):
        return f"{self.coupon.code} → {self.order.code}"
