from django.contrib import admin

from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order", "gateway", "amount", "status", "ref_id", "created_at"]
    list_filter = ["status", "gateway", "created_at"]
    search_fields = ["order__code", "authority", "ref_id"]
    readonly_fields = ["order", "gateway", "amount", "authority", "ref_id",
                       "status", "raw_response", "created_at", "updated_at"]
