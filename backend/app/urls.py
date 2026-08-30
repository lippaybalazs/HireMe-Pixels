from django.urls import path

from .views import pixels, pixel, health


urlpatterns = [
    path("health/", health),
    path("pixels/", pixels),
    path("pixel/", pixel),
]