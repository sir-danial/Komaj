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
    status = models.CharField("وضعیت", max_length=16, choices=STATUS, default=PENDING)

    # --- provider references ---
    # Zibal calls this trackId, Zarinpal calls it authority: the id of the payment
    # session, used for verify and inquiry.
    authority = models.CharField("شناسه تراکنش (trackId)", max_length=128, blank=True, db_index=True)
    # Settlement reference shown to the customer for follow-up (Zibal: refNumber).
    ref_id = models.CharField("شماره پیگیری / مرجع", max_length=128, blank=True)

    # --- card & timing, as reported by the provider ---
    card_number = models.CharField("شماره کارت (ماسک‌شده)", max_length=32, blank=True)
    card_hash = models.CharField("هش شماره کارت", max_length=128, blank=True)
    paid_at = models.DateTimeField("زمان پرداخت", null=True, blank=True)
    verified_at = models.DateTimeField("زمان تأیید", null=True, blank=True)

    # --- provider's own status, kept verbatim for support/reconciliation ---
    gateway_status = models.IntegerField("کد وضعیت درگاه", null=True, blank=True)
    gateway_message = models.CharField("پیام درگاه", max_length=255, blank=True)
    raw_response = models.JSONField("پاسخ خام", default=dict, blank=True)

    created_at = models.DateTimeField("زمان ایجاد", auto_now_add=True)
    updated_at = models.DateTimeField("آخرین بروزرسانی", auto_now=True)

    class Meta:
        verbose_name = "پرداخت"
        verbose_name_plural = "پرداخت‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"پرداخت {self.order.code} — {self.get_status_display()}"

    def apply_details(self, details):
        """Copy a provider's TransactionDetails onto this row.

        Only ever fills in what the provider actually reported — a later inquiry
        that omits a field must not wipe what an earlier verify told us.
        """
        self.ref_id = details.ref_id or self.ref_id
        self.card_number = details.card_number or self.card_number
        self.card_hash = details.card_hash or self.card_hash
        self.paid_at = details.paid_at or self.paid_at
        self.verified_at = details.verified_at or self.verified_at
        if details.status is not None:
            self.gateway_status = details.status
        self.gateway_message = (details.status_label or details.message or "")[:255]
        self.raw_response = details.raw or self.raw_response
