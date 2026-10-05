from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    display_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "telegram_id", "username", "first_name", "last_name", "display_name",
            "photo_url", "language_code", "phone", "is_premium",
        ]
        read_only_fields = [f for f in fields if f != "phone"]


class TelegramAuthSerializer(serializers.Serializer):
    init_data = serializers.CharField(allow_blank=True)
