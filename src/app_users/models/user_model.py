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
        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
        validators=[username_validator],
        blank=False,
        null=False,
    )
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"

    def is_budget_member(self, budget_id: str) -> bool:
        """
        Method to verify if User is member of Budget with given database ID.

        Args:
            budget_id [str]: Budget database id.

        Returns:
            bool: True if User is member of given Budget, False otherwise.
        """
        return bool(self.joined_budgets.filter(pk=budget_id).values("pk"))  # NOQA
