from django.db import models


class Payment(models.Model):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    STATUS = [
        (PENDING, "در انتظار"),
        (PAID, "موفق"),
        (FAILED, "ناموفق"),
    ]

    order = models.ForeignKey(
        "orders.Order", on_delete=models.CASCADE, related_name="payments", verbose_name="سفارش"
    )
    gateway = models.CharField("درگاه", max_length=32)
    amount = models.DecimalField("مبلغ (تومان)", max_digits=14, decimal_places=0)
    authority = models.CharField("کد مرجع", max_length=128, blank=True, db_index=True)
    ref_id = models.CharField("کد پیگیری", max_length=128, blank=True)
    status = models.CharField("وضعیت", max_length=16, choices=STATUS, default=PENDING)
    raw_response = models.JSONField("پاسخ خام", default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"پرداخت {self.order.code} — {self.get_status_display()}"
