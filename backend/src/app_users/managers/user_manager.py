from app_users.models import User
from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Manager for user."""

    def create_user(self, email: str, password: str = None, **extra_fields: dict) -> User:
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
            raise ValueError('Email address not provided for User.')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, password: str) -> User:
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
