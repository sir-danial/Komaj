from django.urls import path

from . import views

app_name = "cart"

urlpatterns = [
    path("cart/", views.cart_detail, name="detail"),
    path("cart/add/", views.cart_add, name="add"),
    path("cart/update/", views.cart_update, name="update"),
    path("cart/remove/", views.cart_remove, name="remove"),
]
