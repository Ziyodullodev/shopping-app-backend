from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import MeView, TelegramAuthView

urlpatterns = [
    path("telegram/", TelegramAuthView.as_view(), name="auth-telegram"),
    path("refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", MeView.as_view(), name="auth-me"),
]
