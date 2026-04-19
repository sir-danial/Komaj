from django.urls import path

from .views import home, healthz, styleguide

urlpatterns = [
    path("", home, name="home"),
    path("healthz/", healthz, name="healthz"),
    path("_styleguide/", styleguide, name="styleguide"),
]
