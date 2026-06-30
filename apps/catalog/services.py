"""Presentation helpers for catalog objects.

Keeps templates dumb and views thin by adapting models into the dict shape the
shared ``components/product_card.html`` expects.
"""
_EN_TO_FA = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def _fa(value):
    return str(value).translate(_EN_TO_FA)


def _trim(decimal_value):
    """'0.50' -> '0.5', '1.00' -> '1' for tidy badges."""
    text = format(decimal_value.normalize(), "f")
    return text


def product_card_context(product):
    """Build the dict consumed by ``components/product_card.html``.

    Prices are in Toman (project convention). The card shows the cheapest active
    variant as a "from" price.
    """
    variant = product.default_variant
    image = product.primary_image

    weight_badge = None
    if variant and variant.is_weighted:
        weight_badge = f"{_fa(_trim(variant.min_order_qty))}kg+"

    return {
        "name": product.name,
        "href": product.get_absolute_url(),
        "image_url": image.url if image else "",
        "image_alt": product.name,
        "price": variant.unit_price if variant else None,
        "unit_label": variant.unit_label if variant else "",
        "weight_badge": weight_badge,
        "is_fresh": product.is_fresh,
        "in_stock": bool(variant and variant.in_stock),
    }
