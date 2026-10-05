from rest_framework.routers import DefaultRouter

from .views import BrandViewSet, ProductViewSet

router = DefaultRouter()
router.register("brands", BrandViewSet, basename="brand")
router.register("products", ProductViewSet, basename="product")

urlpatterns = router.urls
