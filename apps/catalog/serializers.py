from rest_framework import serializers

from .models import Brand, Product, ProductSize


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug", "logo"]


class ProductSizeSerializer(serializers.ModelSerializer):
    in_stock = serializers.SerializerMethodField()

    class Meta:
        model = ProductSize
        fields = ["size", "stock", "in_stock"]

    def get_in_stock(self, obj) -> bool:
        return obj.stock > 0


class ProductListSerializer(serializers.ModelSerializer):
    brand = BrandSerializer(read_only=True)
    is_favorite = serializers.SerializerMethodField()
    default_size = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id", "slug", "name", "brand", "short_description", "price", "old_price",
            "rating", "image", "look", "is_favorite", "default_size",
        ]

    def get_default_size(self, obj) -> int | None:
        """Middle in-stock size, used by the quick "Add" button on product cards."""
        sizes = [s.size for s in obj.sizes.all() if s.stock > 0]
        return sizes[len(sizes) // 2] if sizes else None

    def get_is_favorite(self, obj) -> bool:
        ids = self.context.get("favorite_ids")
        return obj.id in ids if ids is not None else False


class ProductDetailSerializer(ProductListSerializer):
    sizes = ProductSizeSerializer(many=True, read_only=True)

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ["description", "sizes"]
