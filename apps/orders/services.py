"""Turn a session cart into a persisted Order.

Re-validates every line against the live variant (stock/min/step) so a cart that
went stale between "add" and "checkout" fails loudly instead of overselling.
Line prices use the cart's price snapshot (the price the customer saw), per the
research-report risk note on cart-vs-payment price drift.
"""
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.cart.totals import compute_totals, shipping_cost
from apps.cart.totals import shipping_methods as _shipping_methods

from .models import Order, OrderItem


def shipping_method_meta(method_key):
    for m in _shipping_methods(tehran=True):
        if m["key"] == method_key:
            return m
    return None


@transaction.atomic
def create_order_from_cart(cart, data, *, user=None, discount=Decimal("0")):
    """Create a PENDING order from the cart. Does NOT clear the cart or touch
    stock — those happen on confirmed payment.

    ``data`` is the cleaned data of CheckoutForm. Raises ValidationError if the
    cart is empty or a line can no longer be fulfilled.
    """
    items = list(cart)
    if not items:
        raise ValidationError("سبد خرید خالی است.")

    for item in items:
        # re-check availability against the live variant
        item["variant"].validate_quantity(item["quantity"])

    method = shipping_method_meta(data["shipping_method"])
    if method is None:
        raise ValidationError("روش ارسال نامعتبر است.")
    if method["tehran_only"] and data["province"] != "تهران":
        raise ValidationError("پیک تهران فقط برای استان تهران در دسترس است.")

    subtotal = sum((i["line_total"] for i in items), Decimal("0"))
    ship = shipping_cost(method["key"])
    totals = compute_totals(subtotal, shipping=ship, discount=discount)

    order = Order.objects.create(
        user=user if (user and user.is_authenticated) else None,
        receiver_name=data["receiver_name"],
        phone=data["phone"],
        email=data.get("email", ""),
        province=data["province"],
        city=data["city"],
        postal_code=data["postal_code"],
        address_line=data["address_line"],
        note=data.get("note", ""),
        shipping_method=method["key"],
        shipping_label=method["label"],
        subtotal=totals["subtotal"],
        discount=totals["discount"],
        vat_amount=totals["vat"],
        shipping_cost=totals["shipping"],
        total=totals["total"],
    )

    OrderItem.objects.bulk_create([
        OrderItem(
            order=order,
            variant=i["variant"],
            product_name=i["variant"].product.full_name,
            variant_label=i["variant"].label,
            unit_label=i["variant"].unit_label,
            quantity=i["quantity"],
            unit_price=i["unit_price"],
            line_total=i["line_total"],
        )
        for i in items
    ])
    return order
