from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Brand(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(max_length=80, unique=True)
    logo = models.ImageField(upload_to="brands/", blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


def default_look() -> dict:
    return {"upper": "#9a5f33", "sole": "#f2efe9", "accent": "#3b4a5c", "lace": "#6b3e1e"}


class Product(models.Model):
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=160, unique=True)
    short_description = models.CharField(max_length=160, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0"))])
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    rating = models.DecimalField(
        max_digits=2, decimal_places=1, default=Decimal("0"),
        validators=[MinValueValidator(Decimal("0")), MaxValueValidator(Decimal("5"))],
    )
    image = models.ImageField(upload_to="products/", blank=True)
    # Colours for the SVG placeholder used by the frontend when there is no photo.
    look = models.JSONField(default=default_look, blank=True)
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=True)
    sold_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_popular", "-sold_count", "-created_at"]

    def __str__(self) -> str:
        return self.name


class ProductSize(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sizes")
    size = models.PositiveSmallIntegerField(help_text="EU size")
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["size"]
        constraints = [models.UniqueConstraint(fields=["product", "size"], name="uniq_product_size")]

    def __str__(self) -> str:
        return f"{self.product} / {self.size}"
