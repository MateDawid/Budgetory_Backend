import secrets
import string
import uuid

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError

MAX_DEMO_USER_CREATE_ATTEMPTS = 3


def generate_random_password() -> str:
    """
    Generate a secure random password.

    Args:
        length [int]: Length of password (default: 16).

    Returns:
        str: Generated password.
    """
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = "".join(secrets.choice(alphabet) for _ in range(24))
    return password


class UserManager(BaseUserManager):
    """Manager for user."""

    def create_user(self, email: str, password: str, **extra_fields: dict) -> AbstractUser:
        """
        Create, save and return a new user.

        Args:
            email [str]: User email.
            password [str]: User password.
            extra_fields [dict]: Additional data.

        Returns:
            User: Created User model instance.
        """
        if not email:
            raise ValueError("Email address not provided for User.")
        if not password:
            raise ValueError("Password not provided for User.")
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_demo_user(self) -> AbstractUser:
        """
        Create and return demo user.

        Returns:
            User: Created demo User model instance.

        Raises:
            IntegrityError: If unable to create unique user after max_attempts.
        """
        for attempt in range(1, MAX_DEMO_USER_CREATE_ATTEMPTS + 1):
            unique_id = uuid.uuid4().hex[:16]
            user_data = {
                "email": f"{unique_id}@budgetory_demo.com",
                "password": generate_random_password(),
                "is_demo": True,
                "is_active": True,
            }
            try:
                return self.create_user(**user_data)
            except IntegrityError:
                if attempt == MAX_DEMO_USER_CREATE_ATTEMPTS:
                    raise
                continue
        raise IntegrityError("Failed to create demo user after maximum attempts.")

    def create_superuser(self, email: str, password: str) -> AbstractUser:
        """
        Create and return a new superuser.

        Args:
            email [str]: Superuser email.
            password [str]: Superuser password.

        Returns:
            User: Created User model instance.
        """
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user
