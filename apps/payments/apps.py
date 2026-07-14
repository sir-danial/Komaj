from django.apps import AppConfig
from django.conf import settings


class PaymentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.payments"
    verbose_name = "پرداخت‌ها"

    def ready(self):
        from . import scheduler

        interval = getattr(settings, "PAYMENTS_RECONCILE_INTERVAL_MINUTES", 0)
        if interval and scheduler.should_run():
            scheduler.start(interval)
