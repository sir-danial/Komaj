from django.contrib import admin

from .models import Coupon, CouponRedemption


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_type", "value", "min_order_amount",
                    "used_count", "usage_limit", "is_active", "valid_until"]
    list_filter = ["discount_type", "is_active"]
    search_fields = ["code"]
    readonly_fields = ["used_count", "created_at"]


@admin.register(CouponRedemption)
class CouponRedemptionAdmin(admin.ModelAdmin):
    list_display = ["coupon", "order", "amount", "created_at"]
    search_fields = ["coupon__code", "order__code"]
    readonly_fields = ["coupon", "order", "amount", "created_at"]
