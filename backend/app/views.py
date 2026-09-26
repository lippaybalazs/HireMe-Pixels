import msal
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .constants import BOARD_HEIGHT, BOARD_WIDTH, DEFAULT_PIXEL_COLOR
from .models import EntraIdentity, Pixel, PixelHistory
from .serializers import PixelSerializer, PixelUpdateSerializer


def get_msal_app():
    return msal.ConfidentialClientApplication(
        settings.ENTRA_CLIENT_ID,
        authority=f"https://login.microsoftonline.com/{settings.ENTRA_TENANT_ID}",
        client_credential=settings.ENTRA_CLIENT_SECRET,
    )


def microsoft_login(request):
    flow = get_msal_app().initiate_auth_code_flow(
        scopes=[],
        redirect_uri=f"https://{settings.BACKEND_HOSTNAME}/api/auth/callback/",
    )

    request.session["auth_flow"] = flow

    return redirect(flow["auth_uri"])


def callback(request):
    flow = request.session.get("auth_flow")

    if not flow:
        return JsonResponse(
            {"error": "Authentication flow not found."},
            status=400,
        )

    result = get_msal_app().acquire_token_by_auth_code_flow(
        flow,
        request.GET,
    )

    if "error" in result:
        return JsonResponse(
            {
                "error": result.get("error"),
                "description": result.get("error_description"),
            },
            status=400,
        )

    claims = result["id_token_claims"]

    oid = claims["oid"]
    email = claims.get("preferred_username", "")
    name = claims.get("name", "")
    groups = claims.get("groups", [])
    identity = EntraIdentity.objects.select_related("user").filter(oid=oid).first()

    if identity:
        user = identity.user
        user.email = email
        user.first_name = name
        user.save(update_fields=["email", "first_name"])
        identity.email = email
        identity.display_name = name
        identity.save(update_fields=["email", "display_name"])
    else:
        with transaction.atomic():
            user = User.objects.create(
                username=f"entra_{oid}",
                email=email,
                first_name=name,
            )

            EntraIdentity.objects.create(
                user=user,
                oid=oid,
                email=email,
                display_name=name,
            )

    if not user.is_active:
        return JsonResponse(
            {"error": "This user has been banned."},
            status=403,
        )

    django_login(request, user)

    request.session["is_admin"] = settings.ENTRA_ADMIN_GROUP_ID in groups

    request.session.pop("auth_flow", None)

    return redirect(settings.FRONTEND_URL)


@api_view(["POST"])
def register(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if len(username) < 3:
        return Response(
            {"error": "Username must be at least 3 characters long."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 3:
        return Response(
            {"error": "Password must be at least 3 characters long."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if username.lower() == "system":
        return Response(
            {"error": "This username is reserved."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username is already taken."},
            status=status.HTTP_409_CONFLICT,
        )

    user = User.objects.create_user(
        username=username,
        password=password,
    )

    django_login(request, user)

    return Response(
        {
            "message": "Account created.",
            "username": user.username,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["POST"])
def local_login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    user = authenticate(
        request,
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    django_login(request, user)

    return Response(
        {
            "message": "Login successful.",
            "username": user.username,
        }
    )


@api_view(["POST"])
def logout(request):
    django_logout(request)
    return Response({"authenticated": False})


@api_view(["GET"])
def me(request):
    if not request.user.is_authenticated:
        return Response(
            {
                "authenticated": False,
                "is_admin": False,
            },
            status=status.HTTP_200_OK,
        )
    identity = EntraIdentity.objects.filter(user=request.user).first()

    return Response(
        {
            "authenticated": True,
            "username": request.user.username,
            "display_name": identity.display_name if identity else "",
            "auth_provider": "microsoft" if identity else "local",
            "csrf_token": get_token(request),
            "is_admin": request.session.get("is_admin", False),
        }
    )


@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})


@api_view(["GET"])
def pixels(request):
    pixels = Pixel.objects.all()

    grid = [[None] * BOARD_WIDTH for _ in range(BOARD_HEIGHT)]

    for pixel in pixels:
        grid[pixel.y][pixel.x] = pixel.color

    return Response(
        {
            "width": BOARD_WIDTH,
            "height": BOARD_HEIGHT,
            "pixels": grid,
        }
    )


@api_view(["POST"])
def bulk_pixels(request):
    if not request.user.is_authenticated:
        return Response(
            {"error": "You must be logged in to change pixels."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not EntraIdentity.objects.filter(user=request.user).exists():
        return Response(
            {"error": "Microsoft authentication is required."},
            status=status.HTTP_403_FORBIDDEN,
        )

    pixels = request.data.get("pixels")

    if not isinstance(pixels, list) or not pixels:
        return Response(
            {"error": "pixels must be a non-empty list."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    validated_pixels = []

    for item in pixels:
        if not isinstance(item, dict):
            return Response(
                {"error": "Each pixel must be an object."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            x = int(item["x"])
            y = int(item["y"])
            color = item["color"]
        except (KeyError, TypeError, ValueError):
            return Response(
                {"error": "Each pixel must contain x, y and color."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not (0 <= x < BOARD_WIDTH and 0 <= y < BOARD_HEIGHT):
            return Response(
                {"error": "Pixel coordinates are outside the board."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated_pixels.append(
            {
                "x": x,
                "y": y,
                "color": color,
            }
        )

    username = request.user.username
    now = timezone.now()

    with transaction.atomic():
        updated_pixels = []

        for item in validated_pixels:
            try:
                pixel = Pixel.objects.select_for_update().get(
                    x=item["x"],
                    y=item["y"],
                )
            except Pixel.DoesNotExist:
                return Response(
                    {"error": (f"Pixel ({item['x']}, {item['y']}) does not exist.")},
                    status=status.HTTP_404_NOT_FOUND,
                )

            PixelHistory.objects.create(
                x=pixel.x,
                y=pixel.y,
                color=item["color"],
                user=username,
                changed_at=now,
            )

            pixel.color = item["color"]
            pixel.user = username
            pixel.changed_at = now
            pixel.save()

            updated_pixels.append(pixel)

    return Response(PixelSerializer(updated_pixels, many=True).data)


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

        data = PixelSerializer(pixel).data

        identity = EntraIdentity.objects.filter(user__username=pixel.user).first()

        data["user"] = "" if pixel.user == "system" else pixel.user

        data["display_name"] = identity.display_name if identity else "" if pixel.user == "system" else pixel.user

        return Response(data)

    if request.method == "PUT":
        if not request.user.is_authenticated:
            return Response(
                {"error": "You must be logged in to change a pixel."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

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

        username = request.user.username
        now = timezone.now()

        with transaction.atomic():
            PixelHistory.objects.create(
                x=pixel.x,
                y=pixel.y,
                color=data["color"],
                user=username,
                changed_at=now,
            )

            pixel.color = data["color"]
            pixel.user = username
            pixel.changed_at = now
            pixel.save()

        data = PixelSerializer(pixel).data

        identity = EntraIdentity.objects.filter(user__username=pixel.user).first()

        data["user"] = "" if pixel.user == "system" else pixel.user

        data["display_name"] = identity.display_name if identity else "" if pixel.user == "system" else pixel.user

        return Response(data)


@api_view(["POST"])
def ban_user(request):
    if not request.user.is_authenticated:
        return Response(
            {"error": "You must be logged in."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    if not request.session.get("is_admin", False):
        return Response(
            {"error": "You must be an admin."},
            status=status.HTTP_403_FORBIDDEN,
        )

    username = request.data.get("username", "").strip()

    if not username:
        return Response(
            {"error": "Username is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if username == request.user.username:
        return Response(
            {"error": "You cannot ban yourself."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        return Response(
            {"error": "User not found."},
            status=status.HTTP_404_NOT_FOUND,
        )

    with transaction.atomic():
        user_pixels = list(Pixel.objects.select_for_update().filter(user=username))

        for pixel in user_pixels:
            previous = PixelHistory.objects.filter(x=pixel.x, y=pixel.y).exclude(user=username).order_by("-changed_at").first()

            if previous:
                pixel.color = previous.color
                pixel.user = previous.user
                pixel.changed_at = previous.changed_at
            else:
                pixel.color = DEFAULT_PIXEL_COLOR
                pixel.user = "system"
                pixel.changed_at = timezone.now()

            pixel.save(
                update_fields=[
                    "color",
                    "user",
                    "changed_at",
                ]
            )

        PixelHistory.objects.filter(user=username).delete()

        user.is_active = False
        user.save(update_fields=["is_active"])

    return Response(
        {
            "success": True,
            "username": username,
        }
    )
