from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone

from .models import Pixel, PixelHistory
from .constants import BOARD_HEIGHT, BOARD_WIDTH
from .serializers import PixelUpdateSerializer

@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})

@api_view(["GET"])
def pixels(request):
    pixels = Pixel.objects.all()

    grid = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]

    for pixel in pixels:
        grid[pixel.y][pixel.x] = pixel.color

    return Response({
        "width": BOARD_WIDTH,
        "height": BOARD_HEIGHT,
        "pixels": grid,
    })

@api_view(["GET", "PUT"])
def pixel(request):
    if request.method == "GET":
        try:
            x = int(request.query_params["x"])
            y = int(request.query_params["y"])
        except (KeyError, ValueError):
            return Response(
                {"error": "x and y must be integers."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT):
            return Response(
                {"error": "Pixel coordinates are outside the board."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            pixel = Pixel.objects.get(x=x, y=y)
        except Pixel.DoesNotExist:
            return Response(
                {"error": "Pixel does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({
            "x": pixel.x,
            "y": pixel.y,
            "color": pixel.color,
            "user": pixel.user,
            "changed_at": pixel.changed_at,
        })

    if request.method == "PUT":
        serializer = PixelUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data

        try:
            pixel = Pixel.objects.get(
                x=data["x"],
                y=data["y"],
            )
        except Pixel.DoesNotExist:
            return Response(
                {"error": "Pixel does not exist."},
                status=status.HTTP_404_NOT_FOUND,
            )

        now = timezone.now()

        with transaction.atomic():
            PixelHistory.objects.create(
                x=pixel.x,
                y=pixel.y,
                color=data["color"],
                user=data["user"],
                changed_at=now,
            )

            pixel.color = data["color"]
            pixel.user = data["user"]
            pixel.changed_at = now
            pixel.save()

        return Response({
            "x": pixel.x,
            "y": pixel.y,
            "color": pixel.color,
            "user": pixel.user,
            "changed_at": pixel.changed_at,
        })