from django.urls import path

from .views import home, healthz

urlpatterns = [
    path("", home, name="home"),
    path("healthz/", healthz, name="healthz"),
]
