import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from entities.models.choices.deposit_type import DepositType

DEPOSIT_TYPE_URL = reverse("entities:deposit-types")


@pytest.mark.django_db
class TestDepositTypeView:
    """Tests for list view on DepositTypeView."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: DepositType choices defined in application.
        WHEN: Performing HTTP GET request on DEPOSIT_TYPE_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(DEPOSIT_TYPE_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_deposit_type_list(self, api_client: APIClient):
        """
        GIVEN: DepositType choices defined in application.
        WHEN: Performing HTTP GET request on DEPOSIT_TYPE_URL.
        THEN: HTTP_200_OK, choices for DepositType returned.
        """
        response = api_client.get(DEPOSIT_TYPE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [{"value": choice[0], "label": choice[1]} for choice in DepositType.choices]
