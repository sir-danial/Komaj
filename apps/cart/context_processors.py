from .cart import Cart


def cart(request):
    """Expose the cart to every template (header badge, etc.)."""
    c = Cart(request)
    return {"cart": c, "cart_count": c.count}
