import django_filters
from rest_framework import permissions, viewsets

from .models import Brand, Product
from .serializers import BrandSerializer, ProductDetailSerializer, ProductListSerializer


class ProductFilter(django_filters.FilterSet):
    brand = django_filters.CharFilter(field_name="brand__slug")
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr="gte")
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr="lte")
    size = django_filters.NumberFilter(method="filter_size")

    class Meta:
        model = Product
        fields = ["brand", "is_popular"]

    def filter_size(self, qs, name, value):
        return qs.filter(sizes__size=value, sizes__stock__gt=0).distinct()


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BrandSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    lookup_field = "slug"
    queryset = Brand.objects.filter(is_active=True)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    list:   /api/products/?brand=nike&search=white&ordering=price|-price|-rating|-sold_count
    detail: /api/products/{slug}/
    """

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    filterset_class = ProductFilter
    search_fields = ["name", "brand__name", "short_description"]
    ordering_fields = ["price", "rating", "sold_count", "created_at"]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True, brand__is_active=True)
            .select_related("brand")
            .prefetch_related("sizes")
        )

    def get_serializer_class(self):
        return ProductDetailSerializer if self.action == "retrieve" else ProductListSerializer

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            ctx["favorite_ids"] = set(user.favorites.values_list("product_id", flat=True))
        return ctx
