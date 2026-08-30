from django.urls import path

from .views import health, pixel, pixels

urlpatterns = [
    path("health/", health),
    path("pixels/", pixels),
    path("pixel/", pixel),
]
