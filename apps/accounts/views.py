import logging

from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import TelegramAuthSerializer, UserSerializer
from .telegram import InitDataError, validate_init_data

log = logging.getLogger(__name__)

DEV_USER = {"id": 1, "first_name": "Dev", "last_name": "User", "username": "dev_user", "language_code": "en"}


def upsert_telegram_user(tg: dict) -> User:
    defaults = {
        "first_name": (tg.get("first_name") or "")[:150],
        "last_name": (tg.get("last_name") or "")[:150],
        "photo_url": tg.get("photo_url") or "",
        "language_code": tg.get("language_code") or "",
        "is_premium": bool(tg.get("is_premium")),
        "allows_write_to_pm": bool(tg.get("allows_write_to_pm")),
    }
    user = User.objects.filter(telegram_id=tg["id"]).first()
    if user is None:
        user = User(telegram_id=tg["id"], username=f"tg_{tg['id']}")
        user.set_unusable_password()
    for key, value in defaults.items():
        setattr(user, key, value)
    tg_username = tg.get("username")
    if tg_username and not User.objects.filter(username=tg_username).exclude(pk=user.pk).exists():
        user.username = tg_username
    user.save()
    return user


class TelegramAuthView(APIView):
    """Exchange Telegram WebApp initData for a JWT pair."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        init_data = serializer.validated_data["init_data"]

        if not init_data and settings.TELEGRAM_DEV_AUTH:
            tg_user = DEV_USER
        else:
            try:
                parsed = validate_init_data(init_data, settings.TELEGRAM_BOT_TOKEN, settings.TELEGRAM_INIT_DATA_MAX_AGE)
            except InitDataError as exc:
                log.warning("Telegram auth rejected: %s", exc)
                return Response({"detail": f"Telegram auth failed: {exc}"}, status=status.HTTP_401_UNAUTHORIZED)
            tg_user = parsed.user

        user = upsert_telegram_user(tg_user)
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
