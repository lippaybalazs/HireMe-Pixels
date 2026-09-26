from django.urls import path

from . import views

urlpatterns = [
    path("health/", views.health),
    path("pixels/", views.pixels),
    path("pixel/", views.pixel),
    path("bulk_pixels/", views.bulk_pixels),
    path("auth/register/", views.register),
    path("auth/login/", views.local_login),
    path("auth/logout/", views.logout),
    path("auth/ban/", views.ban_user),
    path("auth/me/", views.me),
    path("auth/microsoft/", views.microsoft_login),
    path("auth/callback/", views.callback),
]
