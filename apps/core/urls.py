from django.urls import path

from .views import healthz, home, robots_txt, styleguide

urlpatterns = [
    path("", home, name="home"),
    path("healthz/", healthz, name="healthz"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("_styleguide/", styleguide, name="styleguide"),
]
