from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .constants import BOARD_HEIGHT, BOARD_WIDTH
from .models import Pixel, PixelHistory


class PixelAPITests(APITestCase):
    def setUp(self):
        self.pixel = Pixel.objects.create(
            x=10,
            y=20,
            color="#FFFFFF",
            user="initial-user",
            changed_at=timezone.now(),
        )

    def test_get_pixel(self):
        response = self.client.get(
            "/api/pixel/",
            {"x": 10, "y": 20},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data["x"], 10)
        self.assertEqual(response.data["y"], 20)
        self.assertEqual(response.data["color"], "#FFFFFF")
        self.assertEqual(response.data["user"], "initial-user")

    def test_get_pixel_invalid_coordinates(self):
        response = self.client.get(
            "/api/pixel/",
            {"x": BOARD_WIDTH, "y": 20},
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_get_board(self):
        response = self.client.get("/api/pixels/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["width"],
            BOARD_WIDTH,
        )
        self.assertEqual(
            response.data["height"],
            BOARD_HEIGHT,
        )

        self.assertEqual(
            len(response.data["pixels"]),
            BOARD_HEIGHT,
        )

        self.assertEqual(
            len(response.data["pixels"][0]),
            BOARD_WIDTH,
        )

        self.assertEqual(
            response.data["pixels"][20][10],
            "#FFFFFF",
        )

    def test_update_pixel(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.pixel.refresh_from_db()

        self.assertEqual(
            self.pixel.color,
            "#FF0000",
        )
        self.assertEqual(
            self.pixel.user,
            "bob",
        )

    def test_update_pixel_creates_history(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        history = PixelHistory.objects.get(
            x=10,
            y=20,
        )

        self.assertEqual(
            history.color,
            "#FF0000",
        )
        self.assertEqual(
            history.user,
            "bob",
        )

    def test_update_pixel_updates_current_state_and_history(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#00FF00",
                "user": "alice",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.pixel.refresh_from_db()

        history = PixelHistory.objects.filter(
            x=10,
            y=20,
        ).latest("changed_at")

        self.assertEqual(
            self.pixel.color,
            "#00FF00",
        )
        self.assertEqual(
            self.pixel.user,
            "alice",
        )

        self.assertEqual(
            history.color,
            "#00FF00",
        )
        self.assertEqual(
            history.user,
            "alice",
        )

        self.assertEqual(
            self.pixel.changed_at,
            history.changed_at,
        )

    def test_invalid_color(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#ZZZZZZ",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_x(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": BOARD_WIDTH,
                "y": 20,
                "color": "#FF0000",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_y(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": BOARD_HEIGHT,
                "color": "#FF0000",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_empty_user(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
                "user": "",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_update_nonexistent_pixel(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 50,
                "y": 50,
                "color": "#FF0000",
                "user": "bob",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
