from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartItemView, CartView, FavoriteView, OrderViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/items/", CartItemView.as_view(), name="cart-items"),
    path("cart/items/<int:pk>/", CartItemView.as_view(), name="cart-item"),
    path("favorites/", FavoriteView.as_view(), name="favorites"),
    path("favorites/<slug:slug>/", FavoriteView.as_view(), name="favorite"),
] + router.urls
