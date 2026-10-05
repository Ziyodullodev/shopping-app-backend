from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Shop user. Customers sign in through Telegram, staff can also use a password for the admin."""

    telegram_id = models.BigIntegerField(unique=True, null=True, blank=True, db_index=True)
    photo_url = models.URLField(max_length=500, blank=True)
    language_code = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    is_premium = models.BooleanField(default=False)
    allows_write_to_pm = models.BooleanField(default=False)

    @property
    def display_name(self) -> str:
        full = f"{self.first_name} {self.last_name}".strip()
        return full or (f"@{self.username}" if self.username else f"User {self.pk}")

    def __str__(self) -> str:
        return self.display_name
