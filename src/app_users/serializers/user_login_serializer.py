from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import Token

from app_users.models import User


class UserLoginSerializer(TokenObtainPairSerializer):
    """Class for serializing User model during login."""

    @classmethod
    def get_token(cls, user: User) -> Token:
        """
        Extends Token content with User email.

        Args:
            user (User): User model instance.

        Returns:
            Token: Token class instance.
        """
        token = super().get_token(user)
        token["email"] = user.email
        return token
