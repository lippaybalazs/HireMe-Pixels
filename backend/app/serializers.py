from rest_framework import serializers

from .constants import BOARD_HEIGHT, BOARD_WIDTH
from .models import Pixel


class PixelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pixel
        fields = ["x", "y", "color", "user", "changed_at"]


class PixelUpdateSerializer(serializers.Serializer):
    x = serializers.IntegerField()
    y = serializers.IntegerField()
    color = serializers.CharField(max_length=7)
    user = serializers.CharField(max_length=255)

    def validate_x(self, value):
        if not 0 <= value < BOARD_WIDTH:
            raise serializers.ValidationError(
                f"x must be between 0 and {BOARD_WIDTH - 1}."
            )

        return value

    def validate_y(self, value):
        if not 0 <= value < BOARD_HEIGHT:
            raise serializers.ValidationError(
                f"y must be between 0 and {BOARD_HEIGHT - 1}."
            )

        return value

    def validate_color(self, value):
        if (
            len(value) != 7
            or not value.startswith("#")
            or any(c not in "0123456789abcdefABCDEF" for c in value[1:])
        ):
            raise serializers.ValidationError(
                "Color must be a hex color such as #FF0000."
            )

        return value

    def validate_user(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "User cannot be empty."
            )

        return value