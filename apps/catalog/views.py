from django.shortcuts import get_object_or_404, render

from .models import Category, Product
from .services import product_card_context

HOME_CRUMB = {"href": "/", "label": "خانه"}


def product_list(request, category=None):
    products = (
        Product.objects.filter(is_active=True)
        .select_related("category")
        .prefetch_related("variants", "images")
    )
    if category is not None:
        products = products.filter(category=category)

    if category is not None:
        breadcrumb = [HOME_CRUMB, {"href": "/products/", "label": "محصولات"}, {"label": category.name}]
    else:
        breadcrumb = [HOME_CRUMB, {"label": "محصولات"}]

    cards = [product_card_context(p) for p in products]
    return render(request, "catalog/product_list.html", {
        "category": category,
        "cards": cards,
        "categories": Category.objects.filter(is_active=True),
        "breadcrumb": breadcrumb,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    return product_list(request, category=category)


def product_detail(request, slug):
    product = get_object_or_404(
        Product.objects.select_related("category").prefetch_related("variants", "images"),
        slug=slug,
        is_active=True,
    )
    variants = list(product.variants.filter(is_active=True))
    related = (
        Product.objects.filter(category=product.category, is_active=True)
        .exclude(pk=product.pk)
        .prefetch_related("variants", "images")[:4]
    )
    breadcrumb = [
        HOME_CRUMB,
        {"href": product.category.get_absolute_url(), "label": product.category.name},
        {"label": product.name},
    ]
    return render(request, "catalog/product_detail.html", {
        "product": product,
        "variants": variants,
        "images": list(product.images.all()),
        "related_cards": [product_card_context(p) for p in related],
        "breadcrumb": breadcrumb,
    })
