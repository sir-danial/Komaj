"""Presentation helpers for catalog objects.

Keeps templates dumb and views thin by adapting models into the dict shape the
shared ``components/product_card.html`` expects.
"""
def _abs(request, path):
    return request.build_absolute_uri(path) if request else path


def breadcrumb_jsonld(request, items):
    """BreadcrumbList schema from [{'label','href'?}] (last item = current page).

    Every ListItem gets an absolute ``item`` URL (Google Rich Results best
    practice) — the current-page item falls back to the request path when no
    explicit href is given.
    """
    current = request.path if request else "/"
    elements = []
    for i, item in enumerate(items, start=1):
        elements.append({
            "@type": "ListItem",
            "position": i,
            "name": item["label"],
            "item": _abs(request, item.get("href") or current),
        })
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": elements}


def product_jsonld(request, product):
    """schema.org/Product with offers. Price is emitted in IRR (Rial = Toman×10),
    a valid ISO-4217 code, since schema.org requires a real currency."""
    variant = product.default_variant
    image = product.primary_image
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.full_name,
        "url": _abs(request, product.get_absolute_url()),
        "description": (product.description or product.name)[:500],
        "category": product.category.name,
    }
    if image:
        data["image"] = _abs(request, image.url)
    if product.origin:
        data["brand"] = {"@type": "Brand", "name": product.origin}
    if variant:
        data["sku"] = variant.sku
        data["offers"] = {
            "@type": "Offer",
            "url": _abs(request, product.get_absolute_url()),
            "priceCurrency": "IRR",
            "price": str(int(variant.unit_price) * 10),  # Toman -> Rial
            "availability": (
                "https://schema.org/InStock" if variant.in_stock
                else "https://schema.org/OutOfStock"
            ),
        }
    return data


def product_card_context(product):
    """Build the dict consumed by ``components/product_card.html``.

    Prices are in Toman (project convention). The card shows the cheapest active
    variant as a "from" price.
    """
    variant = product.default_variant
    image = product.primary_image

    # package-size badge, e.g. «جعبه نیم کیلویی» / «ظرف ۴۵۰ گرمی»
    weight_badge = variant.label if variant and variant.label else None

    return {
        "name": product.name,
        "subtitle": product.subtitle,
        "href": product.get_absolute_url(),
        "image_url": image.url if image else "",
        "image_alt": product.full_name,
        "price": variant.unit_price if variant else None,
        "unit_label": variant.unit_label if variant else "",
        "weight_badge": weight_badge,
        "is_fresh": product.is_fresh,
        "in_stock": bool(variant and variant.in_stock),
    }
