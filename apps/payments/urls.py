from django.urls import path

from . import views

app_name = "payments"

urlpatterns = [
    path("payment/start/<str:token>/", views.payment_start, name="start"),
    path("payment/verify/", views.payment_callback, name="callback"),
    path("payment/mock/<str:authority>/", views.mock_gateway, name="mock"),
]
