from django.conf import settings
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.cart.cart import Cart

from .forms import CheckoutForm
from .models import Order
from .services import create_order_from_cart


def _shipping_choices():
    return [
        (m["key"], f'{m["label"]} — {int(m["cost"]):,} تومان')
        for m in settings.SHIPPING_METHODS
    ]


def checkout(request):
    cart = Cart(request)
    if cart.is_empty:
        messages.info(request, "ابتدا محصولی به سبد اضافه کنید.")
        return redirect("cart:detail")

    choices = _shipping_choices()
    initial = {}
    if request.user.is_authenticated:
        initial = {"receiver_name": request.user.get_full_name(), "email": request.user.email}

    if request.method == "POST":
        form = CheckoutForm(request.POST, shipping_choices=choices)
        if form.is_valid():
            from apps.coupons.services import clear_session, record_redemption, session_discount

            coupon, discount = session_discount(request, cart.subtotal)
            try:
                order = create_order_from_cart(
                    cart, form.cleaned_data, user=request.user, discount=discount,
                )
            except ValidationError as exc:
                messages.error(request, exc.messages[0])
                return redirect("cart:detail")
            if coupon and order.discount:
                record_redemption(coupon, order)
                clear_session(request)
            # hand off to the payment gateway (payments app owns this route)
            return redirect(f"/payment/start/{order.token}/")
    else:
        form = CheckoutForm(shipping_choices=choices, initial=initial)

    from apps.coupons.services import session_discount
    coupon, discount = session_discount(request, cart.subtotal)
    return render(request, "orders/checkout.html", {
        "form": form,
        "cart": cart,
        "items": list(cart),
        "totals": cart.totals(discount=discount),
        "coupon": coupon,
        "shipping_methods": settings.SHIPPING_METHODS,
    })


def confirmation(request, token):
    order = get_object_or_404(Order.objects.prefetch_related("items"), token=token)
    return render(request, "orders/confirmation.html", {"order": order})
