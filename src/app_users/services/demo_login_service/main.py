from django.contrib.auth import get_user_model
from django.db import IntegrityError
from rest_framework_simplejwt.tokens import RefreshToken

from app_users.services.demo_login_service.demo_user_initial_data_service import create_initial_data_for_demo_user


def main() -> dict[str, str] | None:
    """
    Main function of demo login service. Creates demo User, initial data and returns demo User token.

    Returns:
        dict[str, str]: Dictionary containing access and refresh token for demo user.
    """
    try:
        user = get_user_model().objects.create_demo_user()
        create_initial_data_for_demo_user(user=user)
    except IntegrityError:
        return None
    refresh = RefreshToken.for_user(user)
    refresh["email"] = user.email
    access = refresh.access_token
    access["email"] = user.email
    return {"refresh": str(refresh), "access": str(access)}
