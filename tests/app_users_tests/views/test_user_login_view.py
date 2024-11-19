import jwt
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

LOGIN_URL: str = reverse("app_users:login")


@pytest.mark.django_db
class TestUserLoginView:
    """Tests for UserLoginView"""

    payload: dict = {
        "email": "test@example.com",
        "password": "test-user-password123",
    }

    def test_login_successful(self, api_client: APIClient):
        """
        GIVEN: User valid payload for login.
        WHEN: UserLoginView.post() called with given data.
        THEN: Token returned.
        """
        get_user_model().objects.create_user(**self.payload)

        response = api_client.post(LOGIN_URL, self.payload)

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        access_payload = jwt.decode(response.data["access"], key=settings.SECRET_KEY, algorithms=["HS256"])
        assert access_payload["token_type"] == "access"
        assert access_payload["email"] == self.payload["email"]
        refresh_payload = jwt.decode(response.data["refresh"], key=settings.SECRET_KEY, algorithms=["HS256"])
        assert refresh_payload["token_type"] == "refresh"
        assert refresh_payload["email"] == self.payload["email"]

    def test_login_not_existing_user(self, api_client: APIClient):
        """
        GIVEN: No User created in database.
        WHEN: UserLoginView.post() called with given data.
        THEN: HTTP 401 returned.
        """
        response = api_client.post(LOGIN_URL, self.payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["detail"] == "No active account found with the given credentials"

    def test_login_with_invalid_password(self, api_client: APIClient):
        """
        GIVEN: User created in database. Invalid password in payload.
        WHEN: UserLoginView.post() called with given data.
        THEN: HTTP 401 returned.
        """
        payload = self.payload.copy()
        get_user_model().objects.create_user(**payload)
        payload["password"] = "wrong"

        response = api_client.post(LOGIN_URL, payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.data["detail"] == "No active account found with the given credentials"
