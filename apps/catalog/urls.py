from django.urls import path

from . import views

app_name = "catalog"

urlpatterns = [
    path("products/", views.product_list, name="product_list"),
    # <str:> (not <slug:>) so Persian/unicode slugs resolve too.
    path("c/<str:slug>/", views.category_detail, name="category"),
    path("p/<str:slug>/", views.product_detail, name="product"),
]
