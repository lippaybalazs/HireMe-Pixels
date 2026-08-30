from django.db import models


class Pixel(models.Model):
    pk = models.CompositePrimaryKey("x", "y")

    x = models.PositiveSmallIntegerField()
    y = models.PositiveSmallIntegerField()
    color = models.CharField(max_length=7)
    user = models.CharField(max_length=255)
    changed_at = models.DateTimeField()


class PixelHistory(models.Model):
    x = models.PositiveSmallIntegerField()
    y = models.PositiveSmallIntegerField()
    color = models.CharField(max_length=7)
    user = models.CharField(max_length=255)
    changed_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(
                fields=["changed_at"],
                name="pixel_history_time_idx",
            ),
        ]
