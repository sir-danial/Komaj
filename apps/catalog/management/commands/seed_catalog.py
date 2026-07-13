"""Seed the catalog with the real Komaj products (brand: سوغات همدان).

Idempotent: re-running updates existing rows by slug/sku rather than
duplicating, attaches missing product images from ``fixtures/seed_images``,
and deactivates any product/variant that is no longer in the lineup.

Sale model: everything is a fixed package with a whole-number quantity —
boxed sweets come in fixed box sizes (نیم/یک/دو کیلویی، هر جعبه یک واریانت با
قیمت خودش) and jar products are ۴۵۰-gram containers sold by count.
Prices are in Toman. Usage: ``python manage.py seed_catalog``.
"""
from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductImage, ProductVariant

SEED_IMAGES = Path(__file__).resolve().parents[2] / "fixtures" / "seed_images"

JAR_GRAMS = 450  # همه ظرف‌ها وزن ثابت ۴۵۰ گرم دارند

CATEGORIES = [
    {"slug": "sweets", "name": "کماج و شیرمال", "sort_order": 1,
     "description": "کماج درجه یک و شیرمال مرغوب همدان — جعبه‌های نیم تا دو کیلویی، تازه از تنور."},
    {"slug": "jars", "name": "حلوا و معجون", "sort_order": 2,
     "description": "حلوا زرده اعلا، انگشت‌پیچ و معجون مخصوص — ظرف‌های ۴۵۰ گرمی سنتی همدان."},
]

PRODUCTS = [
    {
        "slug": "komaj", "name": "کماج درجه یک", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "همدان", "is_featured": True, "is_fresh": True,
        "description": "کماج اصیل همدان، تازه از تنور — سوغات به‌نام همدان در جعبه‌های یک و دو کیلویی.",
        "variants": [
            {"sku": "KOM-1KG", "label": "جعبه یک کیلویی", "weight_grams": 1000,
             "unit_price": "250000", "stock_qty": 30},
            {"sku": "KOM-2KG", "label": "جعبه دو کیلویی", "weight_grams": 2000,
             "unit_price": "500000", "stock_qty": 20},
        ],
        "images": [
            ("komaj-1kg.png", "جعبه یک کیلویی کماج درجه یک"),
            ("komaj-2kg.png", "جعبه دو کیلویی کماج درجه یک"),
        ],
    },
    {
        "slug": "shirmal-korei", "name": "شیرمال مرغوب کره‌ای", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "همدان", "is_featured": False, "is_fresh": True,
        "description": "شیرمال مرغوب کره‌ای — نرم و لطیف با عطر کره، در جعبه‌های نیم، یک و دو کیلویی.",
        "variants": [
            {"sku": "SHK-05KG", "label": "جعبه نیم کیلویی", "weight_grams": 500,
             "unit_price": "110000", "stock_qty": 40},
            {"sku": "SHK-1KG", "label": "جعبه یک کیلویی", "weight_grams": 1000,
             "unit_price": "220000", "stock_qty": 40},
            {"sku": "SHK-2KG", "label": "جعبه دو کیلویی", "weight_grams": 2000,
             "unit_price": "440000", "stock_qty": 20},
        ],
        "images": [
            ("shirmal-korei-1kg.png", "جعبه یک کیلویی شیرمال مرغوب کره‌ای"),
            ("shirmal-korei-05kg.png", "جعبه نیم کیلویی شیرمال مرغوب کره‌ای"),
            ("shirmal-korei-2kg.png", "جعبه دو کیلویی شیرمال مرغوب کره‌ای"),
        ],
    },
    {
        "slug": "shirmal-zafarani", "name": "شیرمال مرغوب زعفرانی", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "همدان", "is_featured": True, "is_fresh": True,
        "description": "شیرمال مرغوب زعفرانی — با زعفران اصل و رنگ و عطر بی‌نظیر، در جعبه‌های نیم، یک و دو کیلویی.",
        "variants": [
            {"sku": "SHZ-05KG", "label": "جعبه نیم کیلویی", "weight_grams": 500,
             "unit_price": "130000", "stock_qty": 40},
            {"sku": "SHZ-1KG", "label": "جعبه یک کیلویی", "weight_grams": 1000,
             "unit_price": "260000", "stock_qty": 40},
            {"sku": "SHZ-2KG", "label": "جعبه دو کیلویی", "weight_grams": 2000,
             "unit_price": "520000", "stock_qty": 20},
        ],
        "images": [
            ("shirmal-zafarani-1kg.png", "جعبه یک کیلویی شیرمال مرغوب زعفرانی"),
            ("shirmal-zafarani-05kg.png", "جعبه نیم کیلویی شیرمال مرغوب زعفرانی"),
            ("shirmal-zafarani-2kg.png", "جعبه دو کیلویی شیرمال مرغوب زعفرانی"),
        ],
    },
    {
        "slug": "halva-zarde", "name": "حلوا زرده اعلا", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": True, "is_fresh": False,
        "description": "حلوا زرده اعلای همدان — حلوای سنتی زعفرانی، سوغات خوش‌عطر بازار همدان در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "HLZ-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "350000", "stock_qty": 30},
        ],
        "images": [("halva-zarde.png", "ظرف حلوا زرده اعلا")],
    },
    {
        "slug": "halva-zarde-heyvani", "name": "حلوا زرده اعلا", "subtitle": "روغن حیوانی",
        "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": False, "is_fresh": False,
        "description": "حلوا زرده اعلا با روغن حیوانی — طعم اصیل و سنتی برای مشتاقان روغن حیوانی، در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "HLZH-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "450000", "stock_qty": 20},
        ],
        "images": [("halva-zarde-heyvani.png", "ظرف حلوا زرده اعلا با روغن حیوانی")],
    },
    {
        "slug": "angosht-pich", "name": "انگشت‌پیچ ویژه", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": True, "is_fresh": False,
        "description": "انگشت‌پیچ ویژه — شیرینی سنتی و خاطره‌انگیز بازار همدان، در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "ANG-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "320000", "stock_qty": 25},
        ],
        "images": [("angosht-pich.png", "ظرف انگشت‌پیچ ویژه")],
    },
    {
        "slug": "majoon", "name": "معجون مخصوص", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": False, "is_fresh": False,
        "description": "معجون مخصوص کماج — ترکیب مقوی و سنتی، همراه همیشگی سفره‌های همدانی، در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "MAJ-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "400000", "stock_qty": 25},
        ],
        "images": [("majoon.png", "ظرف معجون مخصوص")],
    },
]


class Command(BaseCommand):
    help = "بارگذاری کاتالوگ واقعی کماج (idempotent)"

    def handle(self, *args, **options):
        cats = {}
        for data in CATEGORIES:
            cat, _ = Category.objects.update_or_create(
                slug=data["slug"],
                defaults={k: v for k, v in data.items() if k != "slug"},
            )
            cats[data["slug"]] = cat

        for pdata in PRODUCTS:
            pdata = dict(pdata)
            pdata.setdefault("subtitle", "")  # clears a removed subtitle on re-run
            variants = pdata.pop("variants")
            images = pdata.pop("images")
            cat = cats[pdata.pop("category")]
            product, _ = Product.objects.update_or_create(
                slug=pdata["slug"],
                defaults={**{k: v for k, v in pdata.items() if k != "slug"},
                          "category": cat, "is_active": True},
            )
            for vdata in variants:
                ProductVariant.objects.update_or_create(
                    sku=vdata["sku"],
                    defaults={
                        "product": product,
                        "label": vdata.get("label", ""),
                        "weight_grams": vdata.get("weight_grams"),
                        "unit_price": Decimal(vdata["unit_price"]),
                        "min_order_qty": vdata.get("min_order_qty", 1),
                        "stock_qty": vdata["stock_qty"],
                        "is_active": True,
                    },
                )
            # retire variants that fell out of the lineup (e.g. old per-kg SKUs);
            # they may be referenced by past orders, so deactivate — never delete
            product.variants.exclude(sku__in=[v["sku"] for v in variants]).filter(
                is_active=True
            ).update(is_active=False)
            # images are keyed by (product, sort_order): file attaches once,
            # alt text follows the seed on re-runs
            for sort_order, (filename, alt) in enumerate(images):
                existing = ProductImage.objects.filter(
                    product=product, sort_order=sort_order
                ).first()
                if existing:
                    if existing.alt != alt:
                        existing.alt = alt
                        existing.save(update_fields=["alt"])
                    continue
                with (SEED_IMAGES / filename).open("rb") as fh:
                    ProductImage.objects.create(
                        product=product, alt=alt, sort_order=sort_order,
                        image=File(fh, name=filename),
                    )

        # the lineup above is the whole catalog — retire anything else
        lineup_slugs = [p["slug"] for p in PRODUCTS]
        retired = (
            Product.objects.exclude(slug__in=lineup_slugs)
            .filter(is_active=True)
            .update(is_active=False)
        )
        ProductVariant.objects.exclude(product__slug__in=lineup_slugs).filter(
            is_active=True
        ).update(is_active=False)

        self.stdout.write(self.style.SUCCESS(
            f"کاتالوگ کماج بارگذاری شد: {Category.objects.count()} دسته، "
            f"{Product.objects.filter(is_active=True).count()} محصول فعال، "
            f"{ProductVariant.objects.filter(is_active=True, product__is_active=True).count()} نوع فعال"
            + (f"، {retired} محصول قدیمی غیرفعال شد." if retired else ".")
        ))
