from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apps.cart.cart import Cart

from .services import apply_to_session, clear_session


@require_POST
def coupon_apply(request):
    cart = Cart(request)
    code = (request.POST.get("code") or "").strip()
    if not code:
        messages.error(request, "کد تخفیف را وارد کنید.")
        return redirect("cart:detail")
    try:
        coupon = apply_to_session(request, code, cart.subtotal)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect("cart:detail")
    messages.success(request, f"کد تخفیف «{coupon.code}» اعمال شد.")
    return redirect("cart:detail")


@require_POST
def coupon_remove(request):
    clear_session(request)
    messages.info(request, "کد تخفیف حذف شد.")
    return redirect("cart:detail")
