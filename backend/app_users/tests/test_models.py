import pytest
from django.contrib.auth import get_user_model


@pytest.mark.django_db
class TestUserModel:
    """Tests for User model"""

    def test_create_user_successful(self):
        """Test creating a user with an email is successful."""
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(email=email, password=password)

        assert user.email == email
        assert user.check_password(password)

    @pytest.mark.parametrize(
        'email, normalized_email',
        [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ],
    )
    def test_new_user_email_normalized(self, email: str, normalized_email: str):
        """Test email is normalized for new users."""
        user = get_user_model().objects.create_user(email, 'sample123')
        assert user.email == normalized_email

    def test_new_user_without_email_raises_error(self):
        """Test that creating a user without an email raises a ValueError."""
        with pytest.raises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        """Test creating a superuser"""
        user = get_user_model().objects.create_superuser('test@example.com', 'test123')
        assert user.is_superuser is True
        assert user.is_staff is True
