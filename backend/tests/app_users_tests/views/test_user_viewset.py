from typing import Any

import pytest
from app_users.serializers.user_serializer import UserSerializer
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
        assert (
            response.data['detail']['non_field_errors'][0] == 'Unable to authenticate user with provided credentials.'
        )
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
        assert str(response.data['detail']['email'][0]) == 'user with this email already exists.'

    def test_password_too_short_error(self, api_client: APIClient):
        """Test an error is returned if password less than 5 chars."""
        payload = self.payload.copy()
        payload['password'] = 'new'
        response = api_client.post(CREATE_USER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data['detail']['password'][0]) == 'Ensure this field has at least 5 characters.'
        assert not get_user_model().objects.filter(email=payload['email']).exists()


class TestListUserView:
    """Tests for ListUserView"""

    @pytest.mark.django_db
    def test_getting_user_list_as_admin(self, api_client: APIClient, superuser: Any, base_user: Any):
        """Test successful collecting user list as admin user."""
        api_client.force_authenticate(superuser)

        response = api_client.get(LIST_USER_URL)

        users = get_user_model().objects.all().order_by('id')
        serializer = UserSerializer(users, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    @pytest.mark.django_db
    def test_getting_user_list_as_base_user(self, api_client: APIClient, base_user: Any):
        """Test error on collecting user list as base user."""
        api_client.force_authenticate(base_user)
        response = api_client.get(LIST_USER_URL)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'You do not have permission to perform this action.'

    def test_getting_user_list_not_authenticated(self, api_client: APIClient):
        """Test error on collecting user list as unauthenticated user."""
        response = api_client.get(LIST_USER_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(response.data['detail']) == 'Authentication credentials were not provided.'


class TestAuthenticatedUserView:
    """Tests for AuthenticatedUserView"""

    def test_retrieve_user_unauthorized(self, api_client: APIClient):
        """Test error on retrieving user page being unauthenticated."""
        response = api_client.get(ME_URL)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert str(response.data['detail']) == 'Authentication credentials were not provided.'

    @pytest.mark.django_db
    def test_retrieve_profile_success(self, api_client: APIClient, base_user: Any):
        """Test retrieving profile for logged in user."""
        api_client.force_authenticate(base_user)
        response = api_client.get(ME_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == {'name': base_user.name, 'email': base_user.email}

    @pytest.mark.django_db
    def test_post_me_not_allowed(self, api_client: APIClient, base_user: Any):
        """Test POST is not allowed for 'me' endpoint."""
        api_client.force_authenticate(base_user)
        response = api_client.post(ME_URL, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @pytest.mark.django_db
    def test_update_user_profile(self, api_client: APIClient, base_user: Any):
        """Test updating the user profile for the authenticated user."""
        api_client.force_authenticate(base_user)
        payload = {'name': 'Updated name', 'password': 'newpassword123'}

        response = api_client.patch(ME_URL, payload)
        base_user.refresh_from_db()

        assert response.status_code == status.HTTP_200_OK
        assert base_user.name, payload['name']
        assert base_user.check_password(payload['password'])
