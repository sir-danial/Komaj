"""Coupon application via the session.

The applied coupon code lives in ``request.session[COUPON_SESSION_KEY]``. Cart and
checkout call ``session_discount(request, subtotal)`` to resolve the current
coupon + discount, re-validating against the live subtotal every time (a coupon
that no longer qualifies is silently dropped).
"""
from decimal import Decimal

from django.core.exceptions import ValidationError

from .models import Coupon, CouponRedemption

COUPON_SESSION_KEY = "coupon_code"


def validate_coupon(code, subtotal):
    """Return a usable Coupon for ``code``/``subtotal`` or raise ValidationError."""
    try:
        coupon = Coupon.objects.get(code=code.strip().upper())
    except Coupon.DoesNotExist:
        raise ValidationError("کد تخفیف نامعتبر است.")
    error = coupon.availability_error(subtotal)
    if error:
        raise ValidationError(error)
    return coupon


def apply_to_session(request, code, subtotal):
    coupon = validate_coupon(code, subtotal)  # raises if invalid
    request.session[COUPON_SESSION_KEY] = coupon.code
    request.session.modified = True
    return coupon


def clear_session(request):
    request.session.pop(COUPON_SESSION_KEY, None)
    request.session.modified = True


def session_discount(request, subtotal):
    """Resolve the session coupon. Returns (coupon|None, discount Decimal).

    Drops the coupon from the session if it no longer qualifies for the current
    subtotal (e.g. items were removed below the minimum).
    """
    code = request.session.get(COUPON_SESSION_KEY)
    if not code:
        return None, Decimal("0")
    try:
        coupon = validate_coupon(code, subtotal)
    except ValidationError:
        clear_session(request)
        return None, Decimal("0")
    return coupon, coupon.discount_for(subtotal)


def record_redemption(coupon, order):
    """Persist a redemption and bump the usage counter (called on order creation)."""
    CouponRedemption.objects.create(coupon=coupon, order=order, amount=order.discount)
    Coupon.objects.filter(pk=coupon.pk).update(used_count=coupon.used_count + 1)
