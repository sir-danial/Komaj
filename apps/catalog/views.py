from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from .models import Category, Product
from .services import breadcrumb_jsonld, product_card_context, product_jsonld

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
        breadcrumb = [
            HOME_CRUMB,
            {"href": "/products/", "label": "محصولات"},
            {"href": category.get_absolute_url(), "label": category.name},
        ]
    else:
        breadcrumb = [HOME_CRUMB, {"href": "/products/", "label": "محصولات"}]

    cards = [product_card_context(p) for p in products]
    return render(request, "catalog/product_list.html", {
        "category": category,
        "cards": cards,
        "categories": Category.objects.filter(is_active=True),
        "breadcrumb": breadcrumb,
        "jsonld": [breadcrumb_jsonld(request, breadcrumb)],
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
        {"href": product.get_absolute_url(), "label": product.name},
    ]
    return render(request, "catalog/product_detail.html", {
        "product": product,
        "variants": variants,
        "images": list(product.images.all()),
        "related_cards": [product_card_context(p) for p in related],
        "breadcrumb": breadcrumb,
        "jsonld": [product_jsonld(request, product), breadcrumb_jsonld(request, breadcrumb)],
        "og": {
            "type": "product",
            "title": product.name,
            "description": (product.description or product.name)[:200],
            "image": request.build_absolute_uri(product.primary_image.url) if product.primary_image else "",
            "url": request.build_absolute_uri(product.get_absolute_url()),
        },
    })


def search(request):
    query = (request.GET.get("q") or "").strip()
    results = []
    if query:
        products = (
            Product.objects.filter(is_active=True)
            .filter(
                Q(name__icontains=query)
                | Q(description__icontains=query)
                | Q(origin__icontains=query)
                | Q(category__name__icontains=query)
            )
            .select_related("category")
            .prefetch_related("variants", "images")
            .distinct()
        )
        results = [product_card_context(p) for p in products]
    breadcrumb = [HOME_CRUMB, {"href": "/search/", "label": "جستجو"}]
    return render(request, "catalog/search.html", {
        "query": query,
        "cards": results,
        "breadcrumb": breadcrumb,
        "jsonld": [breadcrumb_jsonld(request, breadcrumb)],
        "og": {
            "title": (f"جستجو: {query}" if query else "جستجو") + " — کماج",
            "description": "جستجو در محصولات کماج — شیرینی سنتی و قوطی‌های اصیل ایرانی.",
        },
    })
