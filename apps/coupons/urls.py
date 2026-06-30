from django.urls import path

from . import views

app_name = "coupons"

urlpatterns = [
    path("coupon/apply/", views.coupon_apply, name="apply"),
    path("coupon/remove/", views.coupon_remove, name="remove"),
]
