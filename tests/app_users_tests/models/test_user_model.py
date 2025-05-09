import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestUserModel:
    """Tests for User model"""

    def test_create_user_successful(self):
        """
        GIVEN: User email and password.
        WHEN: UserManager.create_user() called with given data.
        THEN: User created successfully.
        """
        email = "test@example.com"
        username = "Test"
        password = "testpass123"
        user = get_user_model().objects.create_user(email=email, username=username, password=password)

        assert user.email == email
        assert user.username == username
        assert user.check_password(password)

    @pytest.mark.parametrize(
        "email, normalized_email",
        [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["TEST3@EXAMPLE.COM", "TEST3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ],
    )
    def test_new_user_email_normalized(self, email: str, normalized_email: str):
        """
        GIVEN: Not normalized User emails.
        WHEN: UserManager.create_user() called with given data.
        THEN: User created with normalized email.
        """
        user = get_user_model().objects.create_user(email, "Username", "sample123")
        assert user.email == normalized_email

    def test_new_user_without_email_raises_error(self):
        """
        GIVEN: Empty User email.
        WHEN: UserManager.create_user() called with given data.
        THEN: ValueError raised.
        """
        with pytest.raises(ValueError) as exc:
            get_user_model().objects.create_user("", "Username", "test123")
        assert str(exc.value) == "Email address not provided for User."

    def test_new_user_without_username_raises_error(self):
        """
        GIVEN: Empty User username.
        WHEN: UserManager.create_user() called with given data.
        THEN: ValueError raised.
        """
        with pytest.raises(ValueError) as exc:
            get_user_model().objects.create_user("user@example.com", "", "test123")
        assert str(exc.value) == "Username not provided for User."

    def test_new_user_without_password_raises_error(self):
        """
        GIVEN: Empty User password.
        WHEN: UserManager.create_user() called with given data.
        THEN: ValueError raised.
        """
        with pytest.raises(ValueError) as exc:
            get_user_model().objects.create_user("user@example.com", "Username", "")
        assert str(exc.value) == "Password not provided for User."

    def test_create_superuser(self):
        """
        GIVEN: User email and password.
        WHEN: UserManager.create_superuser() called with given data.
        THEN: User with superuser status created.
        """
        user = get_user_model().objects.create_superuser("test@example.com", "Admin", "test123")
        assert user.is_superuser is True
        assert user.is_staff is True
