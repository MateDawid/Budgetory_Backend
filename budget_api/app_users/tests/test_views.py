import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

CREATE_USER_URL = reverse('app_users:create')
TOKEN_URL = reverse('app_users:token')
ME_URL = reverse('app_users:me')
LIST_USER_URL = reverse('app_users:list')


@pytest.mark.django_db
class TestCreateTokenView:
    """Tests for CreateTokenView"""

    payload = {
        'email': 'test@example.com',
        'password': 'test-user-password123',
    }

    def test_create_token_successful(self, api_client: APIClient):
        """Test generating token for valid credentials."""
        get_user_model().objects.create_user(**self.payload, name='TEST_USER')

        response = api_client.post(TOKEN_URL, self.payload)

        assert 'token' in response.data
        assert response.status_code == status.HTTP_200_OK

    def test_create_token_bad_credentials(self, api_client: APIClient):
        """Test returning error if credentials invalid."""
        response = api_client.post(TOKEN_URL, self.payload)

        assert 'token' not in response.data
        assert response.data['non_field_errors'][0] == 'Unable to authenticate user with provided credentials.'
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestCreateUserView:
    """Tests for CreateUserView"""

    payload = {
        'email': 'test@example.com',
        'password': 'testpass123',
        'name': 'Test Name',
    }

    def test_create_user_successful(self, api_client: APIClient):
        """Test successful creation of user."""
        response = api_client.post(CREATE_USER_URL, self.payload)

        assert response.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(email=self.payload['email'])
        assert user.check_password(self.payload['password'])
        assert 'password' not in response.data

    def test_user_with_email_exists_error(self, api_client: APIClient):
        """Test error returned if user with email exists."""
        get_user_model().objects.create_user(**self.payload)
        response = api_client.post(CREATE_USER_URL, self.payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data['email'][0]) == 'user with this email already exists.'

    def test_password_too_short_error(self, api_client: APIClient):
        """Test an error is returned if password less than 5 chars."""
        payload = self.payload.copy()
        payload['password'] = 'new'
        response = api_client.post(CREATE_USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data['password'][0]) == 'Ensure this field has at least 5 characters.'
        assert not get_user_model().objects.filter(email=payload['email']).exists()


class TestListUserView:
    """Tests for ListUserView"""

    pass


class TestAuthenticatedUserView:
    """Tests for AuthenticatedUserView"""

    pass
