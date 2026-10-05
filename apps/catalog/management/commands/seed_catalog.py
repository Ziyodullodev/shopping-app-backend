from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.catalog.models import Brand, Product, ProductSize

DESC = (
    "Lightweight everyday sneaker with a cushioned sole and breathable upper. "
    "Built for comfort from morning walks to late evenings."
)
SHORT = "Lorem ipsum is a placeholder text commonly used"

BRANDS = ["Bata", "Nike", "Adidas", "Wilson", "DSI"]

PRODUCTS = [
    ("casual-brown", "Casual Brown", "Bata", "23.09", "4.7", [39, 40, 41, 42, 43], {"upper": "#9a5f33", "sole": "#f2efe9", "accent": "#3b4a5c", "lace": "#6b3e1e"}),
    ("casual-blue", "Casual Blue", "Bata", "12.09", "4.5", [40, 41, 42, 44], {"upper": "#1f2b45", "sole": "#efe7d8", "accent": "#8a5a33", "lace": "#c9a26a"}),
    ("sport-leather", "Sport leather", "Nike", "33.29", "3.8", [38, 39, 40, 41, 42, 43], {"upper": "#c9ccd1", "sole": "#f7f7f7", "accent": "#aeb3ba", "lace": "#e6e8eb"}),
    ("sport-ride-white", "Sport ride white", "Adidas", "13.54", "4.0", [39, 40, 41, 42], {"upper": "#f6f6f6", "sole": "#ffffff", "accent": "#1f2b45", "lace": "#dadde2"}),
    ("urban-tan", "Urban Tan", "Wilson", "27.50", "4.7", [40, 41, 42, 43, 44], {"upper": "#b8834f", "sole": "#f5f1ea", "accent": "#5a3b22", "lace": "#7a4f2a"}),
    ("cloud-white", "Cloud White", "Nike", "41.00", "4.5", [38, 39, 40, 41], {"upper": "#eef0f3", "sole": "#ffffff", "accent": "#3d7eeb", "lace": "#ffffff"}),
    ("runner-navy", "Runner Navy", "Adidas", "36.20", "4.3", [40, 41, 42, 43], {"upper": "#24365e", "sole": "#e9edf4", "accent": "#3d7eeb", "lace": "#ffffff"}),
    ("trail-olive", "Trail Olive", "DSI", "29.99", "4.1", [41, 42, 43, 44, 45], {"upper": "#5f6b45", "sole": "#3b3b3b", "accent": "#c47a2c", "lace": "#2b2b2b"}),
]


class Command(BaseCommand):
    help = "Create demo brands and products matching the Figma design."

    @transaction.atomic
    def handle(self, *args, **options):
        brands = {}
        for i, name in enumerate(BRANDS):
            brands[name], _ = Brand.objects.update_or_create(slug=name.lower(), defaults={"name": name, "sort_order": i})

        for order, (slug, name, brand, price, rating, sizes, look) in enumerate(PRODUCTS):
            product, _ = Product.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": name, "brand": brands[brand], "price": Decimal(price), "rating": Decimal(rating),
                    "short_description": SHORT, "description": DESC, "look": look,
                    "sold_count": 100 - order * 10,
                },
            )
            for size in sizes:
                ProductSize.objects.get_or_create(product=product, size=size, defaults={"stock": 10})

        self.stdout.write(self.style.SUCCESS(f"Seeded {len(BRANDS)} brands and {len(PRODUCTS)} products."))
