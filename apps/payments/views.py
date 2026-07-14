import logging

from django.conf import settings
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.cart.cart import Cart
from apps.orders.models import Order

from .gateways import PaymentError, get_gateway
from .models import Payment
from .services import verify_and_settle

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
        payment.gateway_message = str(exc)[:255]
        payment.raw_response = {"error": str(exc)}
        payment.save(update_fields=["status", "gateway_message", "raw_response", "updated_at"])
        messages.error(request, "اتصال به درگاه پرداخت ناموفق بود. لطفاً دوباره تلاش کنید.")
        return redirect(order.get_absolute_url())

    payment.authority = init.authority
    payment.raw_response = init.raw
    payment.save(update_fields=["authority", "raw_response", "updated_at"])
    return redirect(init.redirect_url)


def payment_callback(request):
    """Return point from the gateway.

    Zibal sends ?success=1|0&trackId=..&orderId=..&status=..; each gateway parses
    its own shape. The provider's "success" flag is only a hint — the order is
    settled solely on the strength of a successful verify call.
    """
    gateway = get_gateway()
    result = gateway.parse_callback(request.GET)
    if not result.authority:
        raise Http404("callback without a transaction id")

    payment = get_object_or_404(
        Payment.objects.select_related("order"), authority=result.authority
    )
    order = payment.order

    if result.card_hash and not payment.card_hash:
        payment.card_hash = result.card_hash
        payment.save(update_fields=["card_hash", "updated_at"])

    if not result.success:
        if payment.status != Payment.PAID:
            payment.status = Payment.FAILED
            payment.save(update_fields=["status", "updated_at"])
        messages.error(request, "پرداخت ناموفق بود یا لغو شد. می‌توانید دوباره تلاش کنید.")
        return redirect(order.get_absolute_url())

    try:
        settled = verify_and_settle(payment)
    except PaymentError:
        # Couldn't reach the provider to verify. The customer may well have paid,
        # so leave the payment PENDING for reconcile_payments to finish.
        logger.exception("verify unreachable for order %s (trackId %s)",
                         order.code, payment.authority)
        messages.warning(
            request,
            "پرداخت شما انجام شد اما تأیید نهایی با تأخیر مواجه شده است. "
            "وضعیت سفارش به‌زودی به‌روزرسانی می‌شود.",
        )
        return redirect(order.get_absolute_url())

    if settled:
        Cart(request).clear()
        messages.success(request, "پرداخت با موفقیت انجام شد.")
    else:
        messages.error(request, "تأیید پرداخت ناموفق بود. در صورت کسر وجه طی ۷۲ ساعت بازگردانده می‌شود.")
    return redirect(order.get_absolute_url())


def mock_gateway(request, authority):
    """Local stand-in for the bank's StartPay page. Dev only — never in prod."""
    if not getattr(settings, "PAYMENTS_ALLOW_MOCK", settings.DEBUG):
        raise Http404
    payment = get_object_or_404(Payment.objects.select_related("order"), authority=authority)
    callback = reverse("payments:callback")
    return render(request, "payments/mock_gateway.html", {
        "order": payment.order,
        "approve_url": f"{callback}?trackId={authority}&success=1&status=2",
        "cancel_url": f"{callback}?trackId={authority}&success=0&status=3",
    })
