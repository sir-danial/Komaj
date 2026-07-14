"""Recover payments whose callback never reached us.

If the customer pays but never lands back on our callback (closed the tab, lost
their connection, our server was restarting), the order sits PENDING while the
money has actually moved. Worse, Zibal *reverses an unverified transaction back
to the customer's card* — so an unnoticed payment is a lost sale, not just a
stale row.

The same sweep runs automatically inside the web container when
PAYMENTS_RECONCILE_INTERVAL_MINUTES is set (see scheduler.py). This command is
the manual/cron entry point to the identical logic:

    python manage.py reconcile_payments
"""
from django.core.management.base import BaseCommand

from apps.payments.services import (
    DEFAULT_MAX_AGE_HOURS,
    DEFAULT_MIN_AGE_MINUTES,
    reconcile_stale,
    stale_payments,
)


class Command(BaseCommand):
    help = "استعلام پرداخت‌های بلاتکلیف از درگاه و تسویه سفارش‌های پرداخت‌شده"

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-age-minutes", type=int, default=DEFAULT_MIN_AGE_MINUTES,
            help=f"پرداخت‌های جدیدتر از این مقدار نادیده گرفته می‌شوند (پیش‌فرض: {DEFAULT_MIN_AGE_MINUTES}).",
        )
        parser.add_argument(
            "--max-age-hours", type=int, default=DEFAULT_MAX_AGE_HOURS,
            help=f"پرداخت‌های قدیمی‌تر از این مقدار بررسی نمی‌شوند (پیش‌فرض: {DEFAULT_MAX_AGE_HOURS}).",
        )
        parser.add_argument(
            "--dry-run", action="store_true",
            help="فقط گزارش بده؛ چیزی را تغییر نده.",
        )

    def handle(self, *args, **options):
        min_age, max_age = options["min_age_minutes"], options["max_age_hours"]
        pending = stale_payments(min_age, max_age)

        if not pending:
            self.stdout.write("پرداخت بلاتکلیفی برای بررسی وجود ندارد.")
            return

        if options["dry_run"]:
            self.stdout.write(f"[dry-run] {len(pending)} پرداخت بلاتکلیف:")
            for payment in pending:
                self.stdout.write(f"  · سفارش {payment.order.code} (trackId {payment.authority})")
            return

        self.stdout.write(f"بررسی {len(pending)} پرداخت بلاتکلیف…")
        settled, unchanged, errored = reconcile_stale(min_age, max_age, on_result=self._report)
        self.stdout.write(
            f"پایان — تسویه‌شده: {settled}، بدون تغییر/ناموفق: {unchanged}، خطا: {errored}"
        )

    def _report(self, payment, summary, error):
        label = f"سفارش {payment.order.code} (trackId {payment.authority})"
        if error:
            self.stderr.write(self.style.ERROR(f"  ✗ {label}: {error}"))
        elif payment.status == payment.PAID:
            self.stdout.write(self.style.SUCCESS(f"  ✓ {label}: {summary}"))
        else:
            self.stdout.write(f"  · {label}: {summary}")
