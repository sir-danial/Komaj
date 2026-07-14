from django.contrib import admin, messages

from .gateways import PaymentError
from .models import Payment
from .services import reconcile


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "gateway", "amount", "status", "gateway_status_display",
                    "ref_id", "card_number", "paid_at", "created_at"]
    list_filter = ["status", "gateway", "created_at", "paid_at"]
    search_fields = ["order__code", "authority", "ref_id", "card_number"]
    date_hierarchy = "created_at"
    actions = ["inquire_from_gateway"]

    fieldsets = [
        ("سفارش", {"fields": ["order", "gateway", "amount", "status"]}),
        ("شناسه‌های تراکنش", {"fields": ["authority", "ref_id"]}),
        ("اطلاعات کارت و زمان", {
            "fields": ["card_number", "card_hash", "paid_at", "verified_at"]
        }),
        ("وضعیت درگاه", {
            "fields": ["gateway_status", "gateway_status_display", "gateway_message",
                       "raw_response"]
        }),
        ("زمان‌ها", {"fields": ["created_at", "updated_at"]}),
    ]

    readonly_fields = ["order", "gateway", "amount", "status", "authority", "ref_id",
                       "card_number", "card_hash", "paid_at", "verified_at",
                       "gateway_status", "gateway_status_display", "gateway_message",
                       "raw_response", "created_at", "updated_at"]

    @admin.display(description="وضعیت نزد درگاه")
    def gateway_status_display(self, obj):
        if obj.gateway_status is None:
            return "—"
        return f"{obj.gateway_status} — {obj.gateway_message or 'نامشخص'}"

    @admin.display(description="استعلام وضعیت از درگاه و تسویه سفارش")
    def inquire_from_gateway(self, request, queryset):
        """For payments whose callback never arrived: ask the gateway what happened."""
        for payment in queryset.select_related("order"):
            try:
                summary = reconcile(payment)
            except PaymentError as exc:
                self.message_user(
                    request, f"پرداخت {payment.order.code}: خطا در استعلام — {exc}",
                    level=messages.ERROR,
                )
                continue
            self.message_user(request, f"پرداخت {payment.order.code}: {summary}")
