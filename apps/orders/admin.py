from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    readonly_fields = ["variant", "product_name", "variant_label", "unit_label",
                       "quantity", "unit_price", "line_total"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["code", "receiver_name", "phone", "status", "total", "created_at"]
    list_filter = ["status", "province", "shipping_method", "created_at"]
    search_fields = ["code", "receiver_name", "phone", "email"]
    readonly_fields = ["token", "code", "subtotal", "discount", "vat_amount",
                       "shipping_cost", "total", "created_at", "updated_at", "paid_at"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"
