from decimal import Decimal

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render


def _sample_products():
    """Static fallback cards used by the styleguide reference page only.

    The real home page renders DB-backed featured products (see ``home``);
    these samples stay here so ``/_styleguide/`` works without seeded data.
    Prices are in Toman (project convention).
    """
    return [
        {
            "name": "کلمپه کرمانی دست‌ساز",
            "href": "/p/kolompeh/",
            "image_url": "",
            "price": Decimal("180000"),
            "unit_label": "کیلوگرم",
            "weight_badge": "۰.۵kg+",
            "is_fresh": True,
        },
        {
            "name": "باقلوا خانگی با زعفران",
            "href": "/p/baklava/",
            "image_url": "",
            "price": Decimal("220000"),
            "unit_label": "کیلوگرم",
            "weight_badge": "۱kg+",
            "is_fresh": True,
        },
        {
            "name": "شکلات فندقی — قوطی ۲۰۰ گرمی",
            "href": "/p/hazelnut-spread-200/",
            "image_url": "",
            "price": Decimal("120000"),
            "unit_label": "عدد",
            "old_price": Decimal("150000"),
        },
        {
            "name": "ارده سنتی — قوطی ۶۰۰ گرمی",
            "href": "/p/ardeh-600/",
            "image_url": "",
            "price": Decimal("280000"),
            "unit_label": "عدد",
        },
    ]


def home(request):
    from apps.catalog.models import Product
    from apps.catalog.services import product_card_context

    featured = (
        Product.objects.filter(is_active=True, is_featured=True)
        .prefetch_related("variants", "images")[:8]
    )
    cards = [product_card_context(p) for p in featured]
    return render(request, "core/home.html", {
        "featured_products": cards,
        "cart_count": 0,
    })


def styleguide(request):
    swatches = [
        {"name": "cream", "hex": "#FAF6EE"},
        {"name": "espresso", "hex": "#2E1F14"},
        {"name": "saffron", "hex": "#C79A2C"},
        {"name": "pistachio", "hex": "#7A8B3D"},
        {"name": "pomegranate", "hex": "#9C2B3B"},
        {"name": "sand", "hex": "#F0E6D2"},
        {"name": "soft-gold", "hex": "#E8D4A2"},
        {"name": "success", "hex": "#4A7C3C"},
        {"name": "warning", "hex": "#D68A1A"},
        {"name": "error", "hex": "#8E2430"},
    ]
    provinces = [
        ("tehran", "تهران"),
        ("kerman", "کرمان"),
        ("isfahan", "اصفهان"),
        ("shiraz", "فارس"),
    ]
    breadcrumb = [
        {"href": "/", "label": "خانه"},
        {"href": "/c/sweets/", "label": "شیرینی کیلویی"},
        {"href": "#", "label": "کلمپه کرمانی"},
    ]
    return render(request, "core/styleguide.html", {
        "swatches": swatches,
        "provinces": provinces,
        "sample_products": _sample_products(),
        "sample_breadcrumb": breadcrumb,
    })


def healthz(request):
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db_ok = True
    except Exception:
        db_ok = False
    status = 200 if db_ok else 503
    return JsonResponse({"status": "ok" if db_ok else "degraded", "db": db_ok}, status=status)
