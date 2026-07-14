"""Seed the catalog with the real Komaj products (brand: سوغات همدان).

Idempotent: re-running updates existing rows by slug/sku rather than
duplicating, attaches missing product images from ``fixtures/seed_images``,
and deactivates any product/variant that is no longer in the lineup.

Sale model: everything is a fixed package with a whole-number quantity —
boxed sweets come in fixed box sizes (نیم/یک/دو کیلویی، هر جعبه یک واریانت با
قیمت خودش) and jar products are ۴۵۰-gram containers sold by count.
Prices are in Toman. Usage: ``python manage.py seed_catalog``.
"""
import hashlib
from decimal import Decimal
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductImage, ProductVariant

SEED_IMAGES = Path(__file__).resolve().parents[2] / "fixtures" / "seed_images"


def _digest(chunks):
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


def _same_content(stored, source: Path):
    """True when the stored image is byte-identical to the seed file.

    Storage may be the local volume or S3; a missing/unreadable file counts as
    different so the seed re-uploads it.
    """
    try:
        with stored.open("rb") as fh:
            stored_digest = _digest(iter(lambda: fh.read(65536), b""))
    except (FileNotFoundError, ValueError, OSError):
        return False
    with source.open("rb") as fh:
        return stored_digest == _digest(iter(lambda: fh.read(65536), b""))

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
            ("komaj-1kg.png", "جعبه یک کیلویی کماج درجه یک", "KOM-1KG"),
            ("komaj-2kg.png", "جعبه دو کیلویی کماج درجه یک", "KOM-2KG"),
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
            ("shirmal-korei-05kg.png", "جعبه نیم کیلویی شیرمال مرغوب کره‌ای", "SHK-05KG"),
            ("shirmal-korei-1kg.png", "جعبه یک کیلویی شیرمال مرغوب کره‌ای", "SHK-1KG"),
            ("shirmal-korei-2kg.png", "جعبه دو کیلویی شیرمال مرغوب کره‌ای", "SHK-2KG"),
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
            ("shirmal-zafarani-05kg.png", "جعبه نیم کیلویی شیرمال مرغوب زعفرانی", "SHZ-05KG"),
            ("shirmal-zafarani-1kg.png", "جعبه یک کیلویی شیرمال مرغوب زعفرانی", "SHZ-1KG"),
            ("shirmal-zafarani-2kg.png", "جعبه دو کیلویی شیرمال مرغوب زعفرانی", "SHZ-2KG"),
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
        "images": [("halva-zarde.png", "ظرف حلوا زرده اعلا", "HLZ-450")],
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
        "images": [("halva-zarde-heyvani.png", "ظرف حلوا زرده اعلا با روغن حیوانی", "HLZH-450")],
    },
    {
        "slug": "angosht-pich", "name": "انگشت‌پیچ ویژه", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": True, "is_fresh": False,
        "description": "انگشت‌پیچ ویژه — شیرینی سنتی و خاطره‌انگیز بازار همدان، در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "ANG-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "320000", "stock_qty": 25},
        ],
        "images": [("angosht-pich.png", "ظرف انگشت‌پیچ ویژه", "ANG-450")],
    },
    {
        "slug": "majoon", "name": "معجون مخصوص", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "همدان", "is_featured": False, "is_fresh": False,
        "description": "معجون مخصوص کماج — ترکیب مقوی و سنتی، همراه همیشگی سفره‌های همدانی، در ظرف ۴۵۰ گرمی.",
        "variants": [
            {"sku": "MAJ-450", "label": "ظرف ۴۵۰ گرمی", "weight_grams": JAR_GRAMS,
             "unit_price": "400000", "stock_qty": 25},
        ],
        "images": [("majoon.png", "ظرف معجون مخصوص", "MAJ-450")],
    },
]


class Command(BaseCommand):
    help = "بارگذاری کاتالوگ واقعی کماج (idempotent)"

    def handle(self, *args, **options):
        refreshed = 0  # product images whose art changed since the last run
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
                # stock is live operational data (decremented by paid orders,
                # adjusted in admin) — seed it only on first create, never reset
                variant, created = ProductVariant.objects.update_or_create(
                    sku=vdata["sku"],
                    defaults={
                        "product": product,
                        "label": vdata.get("label", ""),
                        "weight_grams": vdata.get("weight_grams"),
                        "unit_price": Decimal(vdata["unit_price"]),
                        "min_order_qty": vdata.get("min_order_qty", 1),
                        "is_active": True,
                    },
                )
                if created:
                    variant.stock_qty = vdata["stock_qty"]
                    variant.save(update_fields=["stock_qty"])
            # retire variants that fell out of the lineup (e.g. old per-kg SKUs);
            # they may be referenced by past orders, so deactivate — never delete
            product.variants.exclude(sku__in=[v["sku"] for v in variants]).filter(
                is_active=True
            ).update(is_active=False)
            # images are keyed by (product, sort_order). The stored file is
            # re-uploaded whenever the seed art changes (compared by content
            # hash) — otherwise a redesigned box/label would never reach a
            # deployed site, whose DB already has the old image row.
            by_sku = {v.sku: v for v in product.variants.all()}
            for sort_order, (filename, alt, sku) in enumerate(images):
                source = SEED_IMAGES / filename
                variant = by_sku.get(sku)
                existing = ProductImage.objects.filter(
                    product=product, sort_order=sort_order
                ).first()
                if existing and _same_content(existing.image, source):
                    if existing.alt != alt or existing.variant_id != (
                        variant.pk if variant else None
                    ):
                        existing.alt = alt
                        existing.variant = variant
                        existing.save(update_fields=["alt", "variant"])
                    continue
                with source.open("rb") as fh:
                    if existing:
                        existing.alt = alt
                        existing.variant = variant
                        # save() the new file under the same row; the old file is
                        # left on disk/S3 rather than risking a live 404 mid-deploy
                        existing.image.save(filename, File(fh), save=False)
                        existing.save(update_fields=["alt", "variant", "image"])
                        refreshed += 1
                    else:
                        ProductImage.objects.create(
                            product=product, variant=variant, alt=alt,
                            sort_order=sort_order, image=File(fh, name=filename),
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
            + (f"، {refreshed} تصویر به‌روزرسانی شد" if refreshed else "")
            + (f"، {retired} محصول قدیمی غیرفعال شد." if retired else ".")
        ))
