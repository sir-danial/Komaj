"""Order-total arithmetic, shared by the cart preview and checkout.

All amounts are Toman (integer Decimals). VAT is computed on the subtotal and
rounded to whole Toman with ROUND_HALF_UP.
"""
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings

WHOLE = Decimal("1")


def vat_for(subtotal):
    return (Decimal(subtotal) * settings.VAT_RATE).quantize(WHOLE, rounding=ROUND_HALF_UP)


def shipping_methods(tehran=True):
    """Available shipping methods. Non-Tehran addresses drop Tehran-only options."""
    methods = settings.SHIPPING_METHODS
    return [m for m in methods if tehran or not m["tehran_only"]]


def shipping_cost(method_key):
    for m in settings.SHIPPING_METHODS:
        if m["key"] == method_key:
            return Decimal(m["cost"])
    return Decimal("0")


def estimate_shipping():
    return shipping_cost(settings.SHIPPING_ESTIMATE_KEY)


def compute_totals(subtotal, shipping=None, discount=Decimal("0")):
    """Return the full money breakdown for a given subtotal.

    discount is applied to the subtotal before VAT (coupon support, phase later).
    """
    subtotal = Decimal(subtotal)
    discount = Decimal(discount)
    if shipping is None:
        shipping = estimate_shipping()
    shipping = Decimal(shipping)

    taxable = max(subtotal - discount, Decimal("0"))
    vat = vat_for(taxable)
    total = taxable + vat + shipping
    return {
        "subtotal": subtotal,
        "discount": discount,
        "vat": vat,
        "shipping": shipping,
        "total": total,
    }
