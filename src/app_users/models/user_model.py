from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

from app_users.managers.user_manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """App User database model."""

    username_validator = UnicodeUsernameValidator()

    email = models.EmailField(max_length=255, unique=True)
    username = models.CharField(
        max_length=150,
        blank=False,
        null=False,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def is_wallet_member(self, wallet_id: str) -> bool:
        """
        Method to verify if User is member of Wallet with given database ID.

        Args:
            wallet_id [str]: Wallet database id.

        Returns:
            bool: True if User is member of given Wallet, False otherwise.
        """
        return self.wallets.filter(pk=wallet_id).exists()
