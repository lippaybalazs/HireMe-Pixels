from django.urls import path

from .views import pixels, pixel


urlpatterns = [
    path("pixels/", pixels),
    path("pixel/", pixel),
]