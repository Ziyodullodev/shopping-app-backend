from django.contrib import admin
from django.utils.html import format_html

from .models import Brand, Product, ProductSize


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "sort_order", "is_active"]
    list_editable = ["sort_order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["thumb", "name", "brand", "price", "rating", "total_stock", "sold_count", "is_popular", "is_active"]
    list_display_links = ["thumb", "name"]
    list_editable = ["price", "is_popular", "is_active"]
    list_filter = ["brand", "is_active", "is_popular"]
    search_fields = ["name", "slug", "brand__name"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductSizeInline]

    @admin.display(description="")
    def thumb(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:40px;border-radius:6px" />', obj.image.url)
        return format_html('<span style="display:inline-block;width:40px;height:24px;border-radius:6px;background:{}"></span>', obj.look.get("upper", "#ccc"))

    @admin.display(description="Stock")
    def total_stock(self, obj):
        return sum(s.stock for s in obj.sizes.all())

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("brand").prefetch_related("sizes")
