from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .constants import BOARD_HEIGHT, BOARD_WIDTH
from .models import EntraIdentity, Pixel, PixelHistory


class PixelAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bob",
            password="password123",
        )

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
        self.assertEqual(response.data["display_name"], "initial-user")

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

    def test_update_pixel_requires_login(self):
        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_update_pixel(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
                "user": "some-other-user",
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

    def test_update_pixel_uses_authenticated_user(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
                "user": "attacker",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.pixel.refresh_from_db()

        self.assertEqual(
            self.pixel.user,
            "bob",
        )

    def test_update_pixel_creates_history(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#FF0000",
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
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#00FF00",
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
            "bob",
        )

        self.assertEqual(
            history.color,
            "#00FF00",
        )
        self.assertEqual(
            history.user,
            "bob",
        )

        self.assertEqual(
            self.pixel.changed_at,
            history.changed_at,
        )

    def test_invalid_color(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": 20,
                "color": "#ZZZZZZ",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_x(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": BOARD_WIDTH,
                "y": 20,
                "color": "#FF0000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_invalid_y(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 10,
                "y": BOARD_HEIGHT,
                "color": "#FF0000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_update_nonexistent_pixel(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.put(
            "/api/pixel/",
            {
                "x": 50,
                "y": 50,
                "color": "#FF0000",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )


class AuthenticationAPITests(APITestCase):
    def test_register(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "alice",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        self.assertEqual(
            response.data["username"],
            "alice",
        )

        self.assertTrue(User.objects.filter(username="alice").exists())

    def test_register_duplicate_username(self):
        User.objects.create_user(
            username="alice",
            password="password123",
        )

        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "alice",
                "password": "another-password",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_409_CONFLICT,
        )

    def test_register_reserved_username(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "system",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_register_short_username(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "ab",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_register_short_password(self):
        response = self.client.post(
            "/api/auth/register/",
            {
                "username": "alice",
                "password": "ab",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_local_login(self):
        User.objects.create_user(
            username="alice",
            password="password123",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "alice",
                "password": "password123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            response.data["username"],
            "alice",
        )

    def test_local_login_invalid_credentials(self):
        User.objects.create_user(
            username="alice",
            password="password123",
        )

        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "alice",
                "password": "wrong-password",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_me_authenticated(self):
        user = User.objects.create_user(
            username="alice",
            password="password123",
        )

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(response.data["authenticated"])

        self.assertEqual(
            response.data["username"],
            "alice",
        )

        self.assertEqual(
            response.data["auth_provider"],
            "local",
        )

        self.assertFalse(response.data["is_admin"])

        self.assertIn(
            "csrf_token",
            response.data,
        )

    def test_me_unauthenticated(self):
        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(response.data["authenticated"])

        self.assertFalse(response.data["is_admin"])

    def test_logout(self):
        user = User.objects.create_user(
            username="alice",
            password="password123",
        )

        self.client.force_authenticate(user=user)

        response = self.client.post("/api/auth/logout/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertFalse(response.data["authenticated"])

    def test_me_microsoft_user(self):
        user = User.objects.create_user(
            username="entra_test-user",
        )

        EntraIdentity.objects.create(
            user=user,
            oid="test-oid",
            email="test@example.com",
            display_name="Test User",
        )

        self.client.force_authenticate(user=user)

        response = self.client.get("/api/auth/me/")

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.assertTrue(response.data["authenticated"])

        self.assertEqual(
            response.data["username"],
            "entra_test-user",
        )

        self.assertEqual(
            response.data["display_name"],
            "Test User",
        )

        self.assertEqual(
            response.data["auth_provider"],
            "microsoft",
        )


class BulkPixelAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="bob",
            password="password123",
        )

        self.pixel_one = Pixel.objects.create(
            x=10,
            y=20,
            color="#FFFFFF",
            user="system",
            changed_at=timezone.now(),
        )

        self.pixel_two = Pixel.objects.create(
            x=11,
            y=20,
            color="#FFFFFF",
            user="system",
            changed_at=timezone.now(),
        )

    def test_bulk_pixels_requires_login(self):
        response = self.client.post(
            "/api/bulk_pixels/",
            {
                "pixels": [
                    {
                        "x": 10,
                        "y": 20,
                        "color": "#FF0000",
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_bulk_pixels_requires_microsoft_authentication(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/bulk_pixels/",
            {
                "pixels": [
                    {
                        "x": 10,
                        "y": 20,
                        "color": "#FF0000",
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_bulk_pixels(self):
        EntraIdentity.objects.create(
            user=self.user,
            oid="test-oid",
            email="test@example.com",
            display_name="Test User",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/bulk_pixels/",
            {
                "pixels": [
                    {
                        "x": 10,
                        "y": 20,
                        "color": "#FF0000",
                    },
                    {
                        "x": 11,
                        "y": 20,
                        "color": "#00FF00",
                    },
                ]
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )

        self.pixel_one.refresh_from_db()
        self.pixel_two.refresh_from_db()

        self.assertEqual(
            self.pixel_one.color,
            "#FF0000",
        )
        self.assertEqual(
            self.pixel_one.user,
            "bob",
        )

        self.assertEqual(
            self.pixel_two.color,
            "#00FF00",
        )
        self.assertEqual(
            self.pixel_two.user,
            "bob",
        )

        self.assertEqual(
            PixelHistory.objects.filter(
                x=10,
                y=20,
                user="bob",
            ).count(),
            1,
        )

        self.assertEqual(
            PixelHistory.objects.filter(
                x=11,
                y=20,
                user="bob",
            ).count(),
            1,
        )

    def test_bulk_pixels_empty_list(self):
        EntraIdentity.objects.create(
            user=self.user,
            oid="test-oid",
            email="test@example.com",
            display_name="Test User",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/bulk_pixels/",
            {
                "pixels": [],
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_bulk_pixels_invalid_coordinates(self):
        EntraIdentity.objects.create(
            user=self.user,
            oid="test-oid",
            email="test@example.com",
            display_name="Test User",
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/bulk_pixels/",
            {
                "pixels": [
                    {
                        "x": BOARD_WIDTH,
                        "y": 20,
                        "color": "#FF0000",
                    }
                ]
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
