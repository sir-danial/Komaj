from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.catalog.models import ProductVariant

from .cart import Cart


def cart_detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {
        "cart": cart,
        "items": list(cart),
        "totals": cart.totals(),
    })


def _parse_quantity(raw):
    try:
        return Decimal(str(raw).replace("٫", ".").replace("،", "").strip())
    except (InvalidOperation, AttributeError, TypeError):
        raise ValidationError("مقدار نامعتبر است.")


@require_POST
def cart_add(request):
    variant = get_object_or_404(
        ProductVariant.objects.select_related("product"),
        pk=request.POST.get("variant_id"), is_active=True,
    )
    try:
        quantity = _parse_quantity(request.POST.get("quantity"))
        cart = Cart(request)
        cart.add(variant, quantity)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
        return redirect(variant.product.get_absolute_url())

    messages.success(request, f"«{variant.product.name}» به سبد اضافه شد.")
    return redirect("cart:detail")


@require_POST
def cart_update(request):
    variant = get_object_or_404(ProductVariant, pk=request.POST.get("variant_id"), is_active=True)
    try:
        quantity = _parse_quantity(request.POST.get("quantity"))
        Cart(request).add(variant, quantity, replace=True)
    except ValidationError as exc:
        messages.error(request, exc.messages[0])
    return redirect("cart:detail")


@require_POST
def cart_remove(request):
    Cart(request).remove(request.POST.get("variant_id"))
    messages.info(request, "کالا از سبد حذف شد.")
    return redirect("cart:detail")
