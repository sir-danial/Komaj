from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_request, name="login"),
    path("login/verify/", views.login_verify, name="verify"),
    path("login/resend/", views.resend_code, name="resend"),
    path("logout/", views.logout_view, name="logout"),
]
