from django.contrib import admin

from .models import Category, Product, ProductImage, ProductVariant


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active", "sort_order"]
    list_editable = ["is_active", "sort_order"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ["image", "variant", "alt", "sort_order"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # only this product's variants may own its images
        if db_field.name == "variant" and request.resolver_match:
            obj_id = request.resolver_match.kwargs.get("object_id")
            if obj_id:
                kwargs["queryset"] = ProductVariant.objects.filter(product_id=obj_id)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = [
        "sku", "label", "weight_grams", "unit_price",
        "min_order_qty", "stock_qty", "is_active",
    ]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "subtitle", "category", "sale_unit", "is_active", "is_featured", "created_at"]
    list_filter = ["category", "sale_unit", "is_active", "is_featured"]
    list_editable = ["is_active", "is_featured"]
    search_fields = ["name", "subtitle", "description", "origin"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]
    autocomplete_fields = ["category"]


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ["sku", "product", "label", "weight_grams", "unit_price", "stock_qty", "is_active"]
    list_filter = ["is_active", "product__sale_unit"]
    search_fields = ["sku", "product__name", "label"]
    autocomplete_fields = ["product"]
