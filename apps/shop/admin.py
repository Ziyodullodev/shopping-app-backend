from django.contrib import admin

from .models import CartItem, Favorite, Order, OrderItem
from .notifications import notify_status_changed


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "size", "price", "quantity", "line_total"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "phone", "total", "payment_method", "is_paid", "status", "created_at"]
    list_filter = ["status", "payment_method", "is_paid", "created_at"]
    list_editable = ["status", "is_paid"]
    search_fields = ["id", "phone", "full_name", "address", "user__username", "user__telegram_id"]
    readonly_fields = ["user", "subtotal", "shipping_fee", "total", "created_at", "updated_at"]
    inlines = [OrderItemInline]
    date_hierarchy = "created_at"

    def save_model(self, request, obj, form, change):
        status_changed = change and "status" in form.changed_data
        super().save_model(request, obj, form, change)
        if status_changed:
            notify_status_changed(obj)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "size", "quantity", "created_at"]
    list_select_related = ["user", "product"]


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ["user", "product", "created_at"]
    list_select_related = ["user", "product"]
