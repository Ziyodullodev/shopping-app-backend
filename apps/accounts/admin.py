from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["id", "display_name", "username", "telegram_id", "phone", "is_staff", "date_joined"]
    search_fields = ["username", "first_name", "last_name", "telegram_id", "phone"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("Telegram", {"fields": ("telegram_id", "photo_url", "language_code", "phone", "is_premium", "allows_write_to_pm")}),
    )
