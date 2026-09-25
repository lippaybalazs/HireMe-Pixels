import msal
from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils import timezone
from django.contrib.auth import authenticate
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.models import User
from django.middleware.csrf import get_token
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .constants import BOARD_HEIGHT, BOARD_WIDTH
from .models import Pixel, PixelHistory, EntraIdentity
from .serializers import PixelUpdateSerializer, PixelSerializer


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
    identity = EntraIdentity.objects.select_related("user").filter(oid=oid).first() 

    if identity: 
        user = identity.user 
        user.email = email 
        user.first_name = name 
        user.save(update_fields=["email", "first_name"]) 
        identity.email = email 
        identity.save(update_fields=["email"]) 
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
            )

    django_login(request, user)

    request.session.pop("auth_flow", None)

    return redirect(settings.FRONTEND_URL)

@api_view(["POST"])
def register(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

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
            {"authenticated": False},
            status=status.HTTP_200_OK,
        )

    return Response(
        {
            "authenticated": True,
            "username": request.user.username,
            "csrf_token": get_token(request),
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

        return Response(PixelSerializer(pixel).data)

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

        return Response(PixelSerializer(pixel).data)