from django.contrib.auth.models import User
from django.db import models


class EntraIdentity(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    oid = models.CharField(max_length=255, unique=True)
    email = models.EmailField(blank=True)
    display_name = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.display_name or self.email or self.oid


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
