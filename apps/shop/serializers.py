from decimal import Decimal

from django.conf import settings
from rest_framework import serializers

from apps.catalog.models import Product
from apps.catalog.serializers import ProductListSerializer

from .models import CartItem, Order, OrderItem


def shipping_fee() -> Decimal:
    return Decimal(str(settings.SHIPPING_FEE))


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "product", "size", "quantity", "line_total"]


class CartAddSerializer(serializers.Serializer):
    product = serializers.SlugRelatedField(slug_field="slug", queryset=Product.objects.filter(is_active=True))
    size = serializers.IntegerField(required=False)
    quantity = serializers.IntegerField(min_value=1, max_value=99, default=1)

    def validate(self, attrs):
        product = attrs["product"]
        sizes = list(product.sizes.filter(stock__gt=0).values_list("size", flat=True))
        if not sizes:
            raise serializers.ValidationError({"product": "Out of stock."})
        size = attrs.get("size")
        if size is None:
            attrs["size"] = sizes[len(sizes) // 2]
        elif size not in sizes:
            raise serializers.ValidationError({"size": "This size is not available."})
        return attrs


class CartSetSerializer(serializers.Serializer):
    product = serializers.SlugRelatedField(slug_field="slug", queryset=Product.objects.filter(is_active=True))
    size = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=0, max_value=99)

    def validate(self, attrs):
        if attrs["quantity"] > 0 and not attrs["product"].sizes.filter(size=attrs["size"]).exists():
            raise serializers.ValidationError({"size": "This size is not available."})
        return attrs


class CartUpdateSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=0, max_value=99)


class OrderItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product_slug", "product_name", "size", "price", "quantity", "line_total"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "status", "status_display", "payment_method", "is_paid", "full_name", "phone",
            "address", "comment", "subtotal", "shipping_fee", "total", "items", "created_at",
        ]
        read_only_fields = ["status", "is_paid", "subtotal", "shipping_fee", "total", "created_at"]


class OrderCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    phone = serializers.CharField(max_length=32)
    address = serializers.CharField(max_length=300)
    comment = serializers.CharField(required=False, allow_blank=True)
    payment_method = serializers.ChoiceField(choices=Order.Payment.choices, default=Order.Payment.CASH)

    def validate_phone(self, value):
        digits = "".join(ch for ch in value if ch.isdigit())
        if len(digits) < 7:
            raise serializers.ValidationError("Enter a valid phone number.")
        return value.strip()


