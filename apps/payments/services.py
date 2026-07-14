"""Settlement logic, shared by the callback view, the admin action, the
``reconcile_payments`` command and the background scheduler.

The invariant everything here protects: an order is settled — marked paid and its
stock decremented — **exactly once**, no matter how many callbacks, retries,
inquiries or concurrent sweeps arrive.
"""
import logging
from datetime import timedelta

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.catalog.models import ProductVariant
from apps.orders.models import Order

from .gateways import PaymentError, get_gateway
from .models import Payment

logger = logging.getLogger(__name__)

# Younger than this, the customer may still be sitting on the bank's page and
# their callback is about to arrive — don't go behind their back.
DEFAULT_MIN_AGE_MINUTES = 15
# Older than this, the provider has long since reversed it; nothing left to do.
DEFAULT_MAX_AGE_HOURS = 72


def verify_and_settle(payment):
    """Verify with the provider under a row lock, then settle the order.

    Returns True if the order is paid (now or already). A double callback is
    harmless: the second one sees PAID and returns early.
    """
    gateway = get_gateway(payment.gateway)

    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        order = Order.objects.select_for_update().get(pk=payment.order_id)

        if payment.status == Payment.PAID or order.is_paid:
            return True  # idempotent: already settled

        details = gateway.verify(payment.authority, order.amount_rial)
        payment.apply_details(details)

        if not details.success:
            payment.status = Payment.FAILED
            payment.save()
            logger.warning(
                "payment verify failed for order %s (trackId %s): %s",
                order.code, payment.authority, details.message,
            )
            return False

        payment.status = Payment.PAID
        payment.save()
        _settle_order(order)

    return True


def reconcile(payment):
    """Recover a payment whose callback never arrived.

    Asks the provider what actually happened, and finishes the job accordingly:
      * paid but not yet verified -> verify now (otherwise Zibal reverses it)
      * paid and already verified -> settle locally; only our DB was behind
      * still awaiting payment     -> leave PENDING, the customer may yet pay
      * anything else (cancelled, refunded, failed) -> mark FAILED

    Returns a short Persian summary of what it did, for the admin/CLI to show.
    """
    if payment.status == Payment.PAID:
        return "قبلاً تسویه شده بود."

    gateway = get_gateway(payment.gateway)
    order = payment.order
    details = gateway.inquiry(payment.authority, order.amount_rial)

    payment.apply_details(details)
    payment.save()

    if details.paid and not details.success:
        # paid, but the amount doesn't match the order — never settle this silently
        logger.error(
            "reconcile: amount mismatch on order %s (trackId %s)", order.code, payment.authority
        )
        return f"مغایرت مبلغ — نیاز به بررسی دستی: {details.message}"

    if details.paid and not details.verified:
        settled = verify_and_settle(payment)
        return "پرداخت تأیید و سفارش تسویه شد." if settled else \
               f"تأیید پرداخت ناموفق بود: {details.message}"

    if details.paid and details.verified:
        # Money captured and finalised at the provider; we simply missed the callback.
        with transaction.atomic():
            locked = Payment.objects.select_for_update().get(pk=payment.pk)
            order = Order.objects.select_for_update().get(pk=locked.order_id)
            if locked.status == Payment.PAID or order.is_paid:
                return "قبلاً تسویه شده بود."
            locked.status = Payment.PAID
            locked.save(update_fields=["status", "updated_at"])
            _settle_order(order)
        return "پرداخت نزد درگاه تأییدشده بود؛ سفارش تسویه شد."

    if details.status is not None and details.status < 0:
        return f"هنوز پرداخت نشده است ({details.status_label})."

    payment.status = Payment.FAILED
    payment.save(update_fields=["status", "updated_at"])
    return f"ناموفق: {details.status_label or details.message}"


def stale_payments(min_age_minutes=DEFAULT_MIN_AGE_MINUTES, max_age_hours=DEFAULT_MAX_AGE_HOURS):
    """Payments left PENDING with a session actually opened at the provider —
    i.e. the ones whose callback may have gone missing."""
    now = timezone.now()
    return Payment.objects.select_related("order").filter(
        status=Payment.PENDING,
        authority__gt="",  # a session was actually opened at the provider
        created_at__lte=now - timedelta(minutes=min_age_minutes),
        created_at__gte=now - timedelta(hours=max_age_hours),
    ).order_by("created_at")


def reconcile_stale(min_age_minutes=DEFAULT_MIN_AGE_MINUTES,
                    max_age_hours=DEFAULT_MAX_AGE_HOURS,
                    on_result=None):
    """Reconcile every stale payment. Shared by the CLI command and the scheduler.

    ``on_result(payment, summary, error)`` is called per payment so callers can
    report however they like. Returns (settled, unchanged, errored).
    """
    settled = unchanged = errored = 0

    for payment in stale_payments(min_age_minutes, max_age_hours):
        try:
            summary = reconcile(payment)
        except PaymentError as exc:
            errored += 1
            logger.warning("reconcile failed for order %s: %s", payment.order.code, exc)
            if on_result:
                on_result(payment, None, exc)
            continue

        payment.refresh_from_db()
        if payment.status == Payment.PAID:
            settled += 1
            logger.info("reconcile settled order %s: %s", payment.order.code, summary)
        else:
            unchanged += 1
        if on_result:
            on_result(payment, summary, None)

    return settled, unchanged, errored


def _settle_order(order):
    """Mark paid and decrement stock. Call inside the transaction, once."""
    order.mark_paid()
    for item in order.items.all():
        ProductVariant.objects.filter(pk=item.variant_id).update(
            stock_qty=F("stock_qty") - item.quantity
        )
    # Low volume + payment already captured: don't fail after capture, but flag
    # any oversell (stock went negative) for admin follow-up.
    oversold = ProductVariant.objects.filter(
        order_items__order=order, stock_qty__lt=0
    ).values_list("sku", flat=True)
    if oversold:
        logger.error("OVERSOLD after paying order %s: variants %s", order.code, list(oversold))
