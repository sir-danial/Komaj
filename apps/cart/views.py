from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import ProductVariant

from .cart import Cart


def cart_detail(request):
    from apps.coupons.services import session_discount

    cart = Cart(request)
    coupon, discount = session_discount(request, cart.subtotal)
    return render(request, "cart/detail.html", {
        "cart": cart,
        "items": list(cart),
        "totals": cart.totals(discount=discount),
        "coupon": coupon,
    })


@require_POST
def cart_add(request):
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=request.POST.get("variant_id"), is_active=True,
    )
    try:
        cart = Cart(request)
        cart.add(variant, request.POST.get("quantity"))
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect(variant.product.get_absolute_url())

    messages.success(request, f"«{variant.product.name}» به سبد اضافه شد.")
    return redirect("cart:detail")


@require_POST
def cart_update(request):
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=request.POST.get("variant_id"), is_active=True,
    )
    try:
        Cart(request).add(variant, request.POST.get("quantity"), replace=True)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("cart:detail")


@require_POST
def cart_remove(request):
    Cart(request).remove(request.POST.get("variant_id"))
    messages.info(request, "کالا از سبد حذف شد.")
    return redirect("cart:detail")
