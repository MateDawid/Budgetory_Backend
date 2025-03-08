import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

REGISTER_URL = reverse("app_users:register")


@pytest.mark.django_db
class TestUserRegisterView:
    """Tests for UserRegisterView"""

    payload = {
        "email": "test@example.com",
        "username": "Test",
        "password_1": "testpass123",
        "password_2": "testpass123",
    }

    def test_create_user_successful(self, api_client: APIClient):
        """
        GIVEN: Payload for User creation.
        WHEN: POST request on CreateUserView.
        THEN: HTTP 201 returned, User created.
        """
        response = api_client.post(REGISTER_URL, self.payload)

        assert response.status_code == status.HTTP_201_CREATED
        user = get_user_model().objects.get(email=self.payload["email"])
        assert user.check_password(self.payload["password_1"])
        assert "password" not in response.data
        assert "password_1" not in response.data
        assert "password_2" not in response.data

    def test_user_with_email_exists_error(self, api_client: APIClient, user_factory: FactoryMetaClass):
        """
        GIVEN: Payload for User creation with duplicated email.
        WHEN: POST request on CreateUserView.
        THEN: HTTP 400 returned.
        """
        user_factory(email=self.payload["email"])
        response = api_client.post(REGISTER_URL, self.payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data["detail"]["email"][0]) == "user with this email already exists."

    def test_password_too_short_error(self, api_client: APIClient):
        """
        GIVEN: Payload for User creation with password too short.
        WHEN: POST request on CreateUserView.
        THEN: HTTP 400 returned.
        """
        payload = self.payload.copy()
        payload["password_1"] = payload["password_2"] = "new"
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data["detail"]["password_1"][0]) == "Ensure this field has at least 8 characters."
        assert str(response.data["detail"]["password_2"][0]) == "Ensure this field has at least 8 characters."
        assert not get_user_model().objects.filter(email=payload["email"]).exists()

    def test_error_passwords_not_the_same_(self, api_client: APIClient):
        """
        GIVEN: Payload for User creation with two different passwords.
        WHEN: POST request on CreateUserView.
        THEN: HTTP 400 returned.
        """
        payload = self.payload.copy()
        payload["password_2"] = "anoth3r_p4ssword"
        response = api_client.post(REGISTER_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert str(response.data["detail"]["non_field_errors"][0]) == "Provided passwords are not the same."
        assert not get_user_model().objects.filter(email=payload["email"]).exists()
