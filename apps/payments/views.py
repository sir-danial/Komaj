import logging

from django.conf import settings
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.cart.cart import Cart
from apps.catalog.models import ProductVariant
from apps.orders.models import Order

from .gateways import PaymentError, get_gateway
from .models import Payment

logger = logging.getLogger(__name__)


def payment_start(request, token):
    order = get_object_or_404(Order, token=token)
    if order.is_paid:
        messages.info(request, "این سفارش قبلاً پرداخت شده است.")
        return redirect(order.get_absolute_url())

    try:
        gateway = get_gateway()  # raises PaymentError in prod if unconfigured
    except PaymentError:
        logger.error("payment gateway not configured for order %s", order.code)
        messages.error(request, "درگاه پرداخت در حال حاضر در دسترس نیست. لطفاً بعداً تلاش کنید.")
        return redirect(order.get_absolute_url())

    payment = Payment.objects.create(order=order, gateway=gateway.name, amount=order.total)
    callback_url = request.build_absolute_uri(reverse("payments:callback"))

    try:
        init = gateway.request(order, callback_url)
    except Exception as exc:  # PaymentError or network/provider errors
        logger.exception("payment request failed for order %s", order.code)
        payment.status = Payment.FAILED
        payment.raw_response = {"error": str(exc)}
        payment.save(update_fields=["status", "raw_response", "updated_at"])
        messages.error(request, "اتصال به درگاه پرداخت ناموفق بود. لطفاً دوباره تلاش کنید.")
        return redirect(order.get_absolute_url())

    payment.authority = init.authority
    payment.raw_response = init.raw
    payment.save(update_fields=["authority", "raw_response", "updated_at"])
    return redirect(init.redirect_url)


def payment_callback(request):
    """Return point from the gateway. Zarinpal sends ?Authority=..&Status=OK|NOK."""
    authority = request.GET.get("Authority") or request.GET.get("authority", "")
    status = request.GET.get("Status") or request.GET.get("status", "")
    payment = get_object_or_404(Payment.objects.select_related("order"), authority=authority)
    order = payment.order

    if status != "OK":
        payment.status = Payment.FAILED
        payment.save(update_fields=["status", "updated_at"])
        messages.error(request, "پرداخت ناموفق بود یا لغو شد. می‌توانید دوباره تلاش کنید.")
        return redirect(order.get_absolute_url())

    success = _verify_and_settle(payment)
    if success:
        Cart(request).clear()
        messages.success(request, "پرداخت با موفقیت انجام شد.")
    else:
        messages.error(request, "تأیید پرداخت ناموفق بود. در صورت کسر وجه طی ۷۲ ساعت بازگردانده می‌شود.")
    return redirect(order.get_absolute_url())


def _verify_and_settle(payment):
    """Verify with the gateway under a row lock so a double callback can't
    settle the order twice or decrement stock twice."""
    gateway = get_gateway()
    with transaction.atomic():
        payment = Payment.objects.select_for_update().get(pk=payment.pk)
        order = Order.objects.select_for_update().get(pk=payment.order_id)

        if payment.status == Payment.PAID or order.is_paid:
            return True  # idempotent: already settled

        result = gateway.verify(payment.authority, order.amount_rial)
        if not result.success:
            payment.status = Payment.FAILED
            payment.raw_response = result.raw
            payment.save(update_fields=["status", "raw_response", "updated_at"])
            return False

        payment.status = Payment.PAID
        payment.ref_id = result.ref_id
        payment.raw_response = result.raw
        payment.save(update_fields=["status", "ref_id", "raw_response", "updated_at"])

        order.mark_paid()
        # decrement stock exactly once, atomically
        for item in order.items.all():
            ProductVariant.objects.filter(pk=item.variant_id).update(
                stock_qty=F("stock_qty") - item.quantity
            )
        # low volume + payment already captured: don't fail after capture, but
        # flag any oversell (stock went negative) for admin follow-up.
        oversold = ProductVariant.objects.filter(
            order_items__order=order, stock_qty__lt=0
        ).values_list("sku", flat=True)
        if oversold:
            logger.error("OVERSOLD after paying order %s: variants %s",
                         order.code, list(oversold))
    return True


def mock_gateway(request, authority):
    """Local stand-in for the bank's StartPay page. Dev only — never in prod."""
    if not getattr(settings, "PAYMENTS_ALLOW_MOCK", settings.DEBUG):
        raise Http404
    payment = get_object_or_404(Payment.objects.select_related("order"), authority=authority)
    callback = reverse("payments:callback")
    return render(request, "payments/mock_gateway.html", {
        "order": payment.order,
        "approve_url": f"{callback}?Authority={authority}&Status=OK",
        "cancel_url": f"{callback}?Authority={authority}&Status=NOK",
    })
