from decimal import Decimal

from django.conf import settings
from django.db import connection
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET


def _sample_products():
    """Static fallback cards used by the styleguide reference page only.

    The real home page renders DB-backed featured products (see ``home``);
    these samples stay here so ``/_styleguide/`` works without seeded data.
    Prices are in Toman (project convention).
    """
    return [
        {
            "name": "کماج درجه یک",
            "href": "/p/komaj/",
            "image_url": "",
            "price": Decimal("250000"),
            "unit_label": "کیلوگرم",
            "weight_badge": "۱kg+",
            "is_fresh": True,
        },
        {
            "name": "شیرمال مرغوب زعفرانی",
            "href": "/p/shirmal-zafarani/",
            "image_url": "",
            "price": Decimal("260000"),
            "unit_label": "کیلوگرم",
            "weight_badge": "۰.۵kg+",
            "is_fresh": True,
        },
        {
            "name": "حلوا زرده اعلا",
            "href": "/p/halva-zarde/",
            "image_url": "",
            "price": Decimal("350000"),
            "unit_label": "عدد",
            "old_price": Decimal("390000"),
        },
        {
            "name": "معجون مخصوص",
            "href": "/p/majoon/",
            "image_url": "",
            "price": Decimal("400000"),
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
    base_url = f"{request.scheme}://{request.get_host()}"
    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "کماج",
            "description": "سوغات اصیل همدان — کماج، شیرمال، حلوا زرده و معجون",
            "url": base_url + "/",
            "logo": base_url + "/static/img/logo-square.png",
            "telephone": "+98-81-38254000",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "همدان",
                "streetAddress": "میدان امام، بازار سنتی",
                "addressCountry": "IR",
            },
        },
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "کماج",
            "url": base_url + "/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": base_url + "/search/?q={search_term_string}",
                "query-input": "required name=search_term_string",
            },
        },
    ]
    return render(request, "core/home.html", {
        "featured_products": cards,
        "cart_count": 0,
        "jsonld": jsonld,
        "og": {
            "title": "کماج — سوغات اصیل همدان",
            "description": "فروشگاه آنلاین کماج — کماج درجه یک، شیرمال، حلوا زرده اعلا و معجون مخصوص همدان، ارسال به سراسر ایران.",
            "url": base_url + "/",
            "image": base_url + "/static/img/logo-square.png",
        },
    })


def styleguide(request):
    # internal QA reference — not for public production traffic
    if not (settings.DEBUG or request.user.is_staff):
        raise Http404
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
        {"href": "/c/sweets/", "label": "کماج و شیرمال"},
        {"href": "#", "label": "کماج درجه یک"},
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


@require_GET
def robots_txt(request):
    sitemap_url = request.build_absolute_uri(reverse("sitemap"))
    lines = [
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /cart/",
        "Disallow: /checkout/",
        "Disallow: /payment/",
        "Disallow: /order/",
        "Disallow: /login/",
        "Disallow: /_styleguide/",
        f"Sitemap: {sitemap_url}",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")
