from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken


def get_demo_user_token() -> dict[str, str] | None:
    """
    Creates demo user and returns its token.

    Returns:
        dict[str, str]: Dictionary containing access and refresh token for demo user.
    """
    try:
        user = get_user_model().objects.create_demo_user()
    except IntegrityError:
        return None
    refresh = RefreshToken.for_user(user)
    refresh["email"] = user.email
    access = refresh.access_token
    access["email"] = user.email
    return {"refresh": str(refresh), "access": str(access)}
