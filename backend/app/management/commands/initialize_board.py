from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from app.constants import BOARD_HEIGHT, BOARD_WIDTH, DEFAULT_PIXEL_COLOR
from app.models import Pixel


class Command(BaseCommand):
    help = "Initialize the pixel board with white pixels."

    def handle(self, *args, **options):
        now = timezone.now()

        pixels = [
            Pixel(
                x=x,
                y=y,
                color=DEFAULT_PIXEL_COLOR,
                user="system",
                changed_at=now,
            )
            for y in range(BOARD_HEIGHT)
            for x in range(BOARD_WIDTH)
        ]

        with transaction.atomic():
            Pixel.objects.bulk_create(
                pixels,
                ignore_conflicts=True,
            )

        self.stdout.write(self.style.SUCCESS(f"Board initialized: {BOARD_WIDTH}x{BOARD_HEIGHT} pixels."))
