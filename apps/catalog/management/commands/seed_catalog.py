"""Seed the catalog with sample categories, products and variants.

Idempotent: re-running updates existing rows by slug/sku rather than duplicating.
Prices are in Toman. Usage: ``python manage.py seed_catalog``.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, ProductVariant

CATEGORIES = [
    {"slug": "sweets", "name": "شیرینی کیلویی", "sort_order": 1,
     "description": "کلمپه، باقلوا، سوهان و شیرینی‌های سنتی دست‌ساز — وزنی و تازه‌پخت."},
    {"slug": "jars", "name": "قوطی‌های مکمل", "sort_order": 2,
     "description": "شکلات، ارده، حلوا و کره‌های سنتی در قوطی‌های آماده."},
]

PRODUCTS = [
    {
        "slug": "kolompeh", "name": "کلمپه کرمانی دست‌ساز", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "کرمان", "is_featured": True, "is_fresh": True,
        "description": "کلمپه سنتی کرمان با مغز خرما و گردو، تازه‌پخت.",
        "variants": [
            {"sku": "KOL-KG", "is_weighted": True, "unit_price": "180000",
             "min_order_qty": "0.5", "qty_step": "0.5", "stock_qty": "40"},
        ],
    },
    {
        "slug": "baklava", "name": "باقلوا خانگی با زعفران", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "یزد", "is_featured": True, "is_fresh": True,
        "description": "باقلوای لایه‌ای با مغز پسته و زعفران اصل، شربت ملایم.",
        "variants": [
            {"sku": "BAK-KG", "is_weighted": True, "unit_price": "320000",
             "min_order_qty": "0.5", "qty_step": "0.25", "stock_qty": "25"},
        ],
    },
    {
        "slug": "sohan", "name": "سوهان عسلی قم", "category": "sweets",
        "sale_unit": Product.WEIGHT, "origin": "قم", "is_featured": False, "is_fresh": True,
        "description": "سوهان عسلی با مغز پسته و بادام.",
        "variants": [
            {"sku": "SOH-KG", "is_weighted": True, "unit_price": "260000",
             "min_order_qty": "0.5", "qty_step": "0.5", "stock_qty": "30"},
        ],
    },
    {
        "slug": "hazelnut-spread", "name": "شکلات صبحانه فندقی", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "", "is_featured": True, "is_fresh": False,
        "description": "کرم شکلات فندقی بدون مواد نگهدارنده، در دو اندازه قوطی.",
        "variants": [
            {"sku": "HAZ-200", "label": "قوطی ۲۰۰ گرمی", "weight_grams": 200,
             "is_weighted": False, "unit_price": "120000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "60"},
            {"sku": "HAZ-600", "label": "قوطی ۶۰۰ گرمی", "weight_grams": 600,
             "is_weighted": False, "unit_price": "300000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "35"},
        ],
    },
    {
        "slug": "ardeh", "name": "ارده سنتی", "category": "jars",
        "sale_unit": Product.PIECE, "origin": "", "is_featured": True, "is_fresh": False,
        "description": "ارده خالص از کنجد بوداده، قوطی ۶۰۰ گرمی.",
        "variants": [
            {"sku": "ARD-600", "label": "قوطی ۶۰۰ گرمی", "weight_grams": 600,
             "is_weighted": False, "unit_price": "280000",
             "min_order_qty": "1", "qty_step": "1", "stock_qty": "20"},
        ],
    },
]


class Command(BaseCommand):
    help = "بارگذاری داده‌ی نمونه کاتالوگ (idempotent)"

    def handle(self, *args, **options):
        cats = {}
        for data in CATEGORIES:
            cat, _ = Category.objects.update_or_create(
                slug=data["slug"],
                defaults={k: v for k, v in data.items() if k != "slug"},
            )
            cats[data["slug"]] = cat

        for pdata in PRODUCTS:
            variants = pdata.pop("variants")
            cat = cats[pdata.pop("category")]
            product, _ = Product.objects.update_or_create(
                slug=pdata["slug"],
                defaults={**{k: v for k, v in pdata.items() if k != "slug"}, "category": cat},
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

        self.stdout.write(self.style.SUCCESS(
            f"کاتالوگ نمونه بارگذاری شد: {Category.objects.count()} دسته، "
            f"{Product.objects.count()} محصول، {ProductVariant.objects.count()} نوع."
        ))
