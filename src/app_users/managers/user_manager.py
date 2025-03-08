from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser


class UserManager(BaseUserManager):
    """Manager for user."""

    def create_user(self, email: str, username: str, password: str, **extra_fields: dict) -> AbstractUser:
        """
        Create, save and return a new user.

        Args:
            email [str]: User email.
            username [str]: User username.
            password [str]: User password.
            extra_fields [dict]: Additional data.

        Returns:
            User: Created User model instance.
        """
        if not email:
            raise ValueError("Email address not provided for User.")
        if not username:
            raise ValueError("Username not provided for User.")
        if not password:
            raise ValueError("Password not provided for User.")
        user = self.model(email=self.normalize_email(email), username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email: str, username: str, password: str) -> AbstractUser:
        """
        Create and return a new superuser.

        Args:
            email [str]: Superuser email.
            password [str]: Superuser password.

        Returns:
            User: Created User model instance.
        """
        user = self.create_user(email, username, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user
