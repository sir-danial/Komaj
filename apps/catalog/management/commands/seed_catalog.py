"""Seed the catalog with the real Komaj products (brand: سوغات همدان).

Idempotent: re-running updates existing rows by slug/sku rather than
duplicating, attaches missing product images from ``fixtures/seed_images``,
and deactivates any product that is no longer in the lineup.
Prices are in Toman. Usage: ``python manage.py seed_catalog``.
"""
from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductImage, ProductVariant

SEED_IMAGES = Path(__file__).resolve().parents[2] / "fixtures" / "seed_images"

CATEGORIES = [
    {"slug": "sweets", "name": "کماج و شیرمال", "sort_order": 1,
     "description": "کماج درجه یک و شیرمال مرغوب همدان — جعبه‌های نیم تا دو کیلویی، تازه از تنور."},
    {"slug": "jars", "name": "حلوا و معجون", "sort_order": 2,
     "description": "حلوا زرده اعلا، انگشت‌پیچ و معجون مخصوص — ظرف‌های سنتی همدان."},
]

PRODUCTS = [
    {
        "slug": "komaj", "name": "کماج درجه یک", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "همدان", "is_featured": True, "is_fresh": True,
        "description": "کماج اصیل همدان، تازه از تنور — سوغات به‌نام همدان در جعبه‌های یک و دو کیلویی.",
        "variants": [
            {"sku": "KOM-KG", "is_weighted": True, "unit_price": "250000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "50"},
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
            {"sku": "SHK-KG", "is_weighted": True, "unit_price": "220000",
             "min_order_qty": "0.5", "qty_step": "0.5", "stock_qty": "60"},
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
            {"sku": "SHZ-KG", "is_weighted": True, "unit_price": "260000",
             "min_order_qty": "0.5", "qty_step": "0.5", "stock_qty": "60"},
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
        "description": "حلوا زرده اعلای همدان — حلوای سنتی زعفرانی، سوغات خوش‌عطر بازار همدان در ظرف آماده.",
        "variants": [
            {"sku": "HLZ-1", "label": "ظرف", "is_weighted": False, "unit_price": "350000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "30"},
        ],
        "images": [("halva-zarde.png", "ظرف حلوا زرده اعلا")],
    },
    {
        "slug": "halva-zarde-heyvani", "name": "حلوا زرده اعلا (روغن حیوانی)", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": False, "is_fresh": False,
        "description": "حلوا زرده اعلا با روغن حیوانی — طعم اصیل و سنتی برای مشتاقان روغن حیوانی، در ظرف آماده.",
        "variants": [
            {"sku": "HLZH-1", "label": "ظرف", "is_weighted": False, "unit_price": "450000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "20"},
        ],
        "images": [("halva-zarde-heyvani.png", "ظرف حلوا زرده اعلا با روغن حیوانی")],
    },
    {
        "slug": "angosht-pich", "name": "انگشت‌پیچ اعلا", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": True, "is_fresh": False,
        "description": "انگشت‌پیچ اعلا — شیرینی سنتی و خاطره‌انگیز بازار همدان، در ظرف آماده.",
        "variants": [
            {"sku": "ANG-1", "label": "ظرف", "is_weighted": False, "unit_price": "320000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "25"},
        ],
        "images": [("angosht-pich.png", "ظرف انگشت‌پیچ اعلا")],
    },
    {
        "slug": "majoon", "name": "معجون مخصوص", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": False, "is_fresh": False,
        "description": "معجون مخصوص کماج — ترکیب مقوی و سنتی، همراه همیشگی سفره‌های همدانی، در ظرف آماده.",
        "variants": [
            {"sku": "MAJ-1", "label": "ظرف", "is_weighted": False, "unit_price": "400000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "25"},
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
                        "is_weighted": vdata["is_weighted"],
                        "unit_price": Decimal(vdata["unit_price"]),
                        "min_order_qty": Decimal(vdata["min_order_qty"]),
                        "qty_step": Decimal(vdata["qty_step"]),
                        "stock_qty": Decimal(vdata["stock_qty"]),
                        "is_active": True,
                    },
                )
            for sort_order, (filename, alt) in enumerate(images):
                if ProductImage.objects.filter(product=product, alt=alt).exists():
                    continue
                with (SEED_IMAGES / filename).open("rb") as fh:
                    ProductImage.objects.create(
                        product=product, alt=alt, sort_order=sort_order,
                        image=File(fh, name=filename),
                    )

        # the lineup above is the whole catalog — retire anything else
        retired = (
            Product.objects.exclude(slug__in=[p["slug"] for p in PRODUCTS])
            .filter(is_active=True)
            .update(is_active=False)
        )

        self.stdout.write(self.style.SUCCESS(
            f"کاتالوگ کماج بارگذاری شد: {Category.objects.count()} دسته، "
            f"{Product.objects.filter(is_active=True).count()} محصول فعال، "
            f"{ProductVariant.objects.count()} نوع"
            + (f"، {retired} محصول قدیمی غیرفعال شد." if retired else ".")
        ))
