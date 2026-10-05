from django.db import transaction
from django.db.models import F
from django.shortcuts import get_object_or_404
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import Product, ProductSize
from apps.catalog.serializers import ProductListSerializer

from .models import CartItem, Favorite, Order, OrderItem
from .notifications import notify_order_created
from .serializers import (
    CartAddSerializer, CartItemSerializer, CartSetSerializer, CartUpdateSerializer, OrderCreateSerializer,
    OrderSerializer, shipping_fee,
)


def cart_payload(user, request):
    items = list(
        CartItem.objects.filter(user=user).select_related("product__brand").prefetch_related("product__sizes")
    )
    fav_ids = set(user.favorites.values_list("product_id", flat=True))
    subtotal = sum((i.line_total for i in items), start=0)
    fee = shipping_fee() if items else 0
    return {
        "items": CartItemSerializer(items, many=True, context={"request": request, "favorite_ids": fav_ids}).data,
        "count": sum(i.quantity for i in items),
        "subtotal": f"{subtotal:.2f}",
        "shipping_fee": f"{fee:.2f}",
        "total": f"{subtotal + fee:.2f}",
    }


class CartView(APIView):
    """GET the cart, DELETE to clear it."""

    def get(self, request):
        return Response(cart_payload(request.user, request))

    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response(cart_payload(request.user, request))


class CartItemView(APIView):
    """
    POST  /api/cart/items/       {product, size?, quantity?} adds to (increments) a line.
    PUT   /api/cart/items/       {product, size, quantity} sets the exact quantity, 0 removes the line.
    PATCH /api/cart/items/{id}/  {quantity} edits a line, DELETE removes it.
    """

    def post(self, request):
        s = CartAddSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        product, size, qty = s.validated_data["product"], s.validated_data["size"], s.validated_data["quantity"]
        item, created = CartItem.objects.get_or_create(
            user=request.user, product=product, size=size, defaults={"quantity": qty}
        )
        if not created:
            item.quantity = F("quantity") + qty
            item.save(update_fields=["quantity"])
        return Response(cart_payload(request.user, request), status=status.HTTP_201_CREATED)

    def put(self, request):
        s = CartSetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        product, size, qty = s.validated_data["product"], s.validated_data["size"], s.validated_data["quantity"]
        if qty == 0:
            CartItem.objects.filter(user=request.user, product=product, size=size).delete()
        else:
            CartItem.objects.update_or_create(
                user=request.user, product=product, size=size, defaults={"quantity": qty}
            )
        return Response(cart_payload(request.user, request))

    def patch(self, request, pk):
        item = get_object_or_404(CartItem, pk=pk, user=request.user)
        s = CartUpdateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        if s.validated_data["quantity"] == 0:
            item.delete()
        else:
            item.quantity = s.validated_data["quantity"]
            item.save(update_fields=["quantity"])
        return Response(cart_payload(request.user, request))

    def delete(self, request, pk):
        get_object_or_404(CartItem, pk=pk, user=request.user).delete()
        return Response(cart_payload(request.user, request))


class FavoriteView(APIView):
    """GET lists wishlist products. POST {product: slug} adds, DELETE /api/favorites/{slug}/ removes."""

    def get(self, request):
        products = (
            Product.objects.filter(favorited_by__user=request.user, is_active=True)
            .select_related("brand")
            .prefetch_related("sizes")
        )
        ids = {p.id for p in products}
        return Response(ProductListSerializer(products, many=True, context={"request": request, "favorite_ids": ids}).data)

    def post(self, request):
        product = get_object_or_404(Product, slug=request.data.get("product"), is_active=True)
        Favorite.objects.get_or_create(user=request.user, product=product)
        return Response({"product": product.slug, "is_favorite": True}, status=status.HTTP_201_CREATED)

    def delete(self, request, slug):
        Favorite.objects.filter(user=request.user, product__slug=slug).delete()
        return Response({"product": slug, "is_favorite": False})


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    filterset_fields = ["status"]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related("items")

    def create(self, request, *args, **kwargs):
        s = OrderCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = request.user

        with transaction.atomic():
            items = list(CartItem.objects.filter(user=user).select_related("product").select_for_update())
            if not items:
                return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

            # Reserve stock; fail the whole order if any size ran out.
            problems = []
            for item in items:
                updated = ProductSize.objects.filter(
                    product=item.product, size=item.size, stock__gte=item.quantity
                ).update(stock=F("stock") - item.quantity)
                if not updated:
                    problems.append(f"{item.product.name} (EU {item.size})")
            if problems:
                transaction.set_rollback(True)
                return Response(
                    {"detail": "Not enough stock for: " + ", ".join(problems)}, status=status.HTTP_409_CONFLICT
                )

            subtotal = sum((i.line_total for i in items), start=0)
            fee = shipping_fee()
            order = Order.objects.create(
                user=user, subtotal=subtotal, shipping_fee=fee, total=subtotal + fee, **s.validated_data
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order, product=i.product, product_name=i.product.name, product_slug=i.product.slug,
                    size=i.size, price=i.product.price, quantity=i.quantity,
                ) for i in items
            ])
            for i in items:
                Product.objects.filter(pk=i.product_id).update(sold_count=F("sold_count") + i.quantity)
            CartItem.objects.filter(user=user).delete()
            if s.validated_data.get("phone") and not user.phone:
                user.phone = s.validated_data["phone"]
                user.save(update_fields=["phone"])
            transaction.on_commit(lambda: notify_order_created(order))

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.status != Order.Status.NEW:
            return Response({"detail": "Only new orders can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)
        with transaction.atomic():
            for item in order.items.all():
                if item.product_id:
                    ProductSize.objects.filter(product_id=item.product_id, size=item.size).update(
                        stock=F("stock") + item.quantity
                    )
            order.status = Order.Status.CANCELLED
            order.save(update_fields=["status", "updated_at"])
        return Response(OrderSerializer(order).data)


