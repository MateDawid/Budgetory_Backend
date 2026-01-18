import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models import Currency
from wallets.serializers.currency_serializer import CurrencySerializer

CURRENCIES_URL = reverse("currency")


@pytest.mark.django_db
class TestCurrencyViewSetList:
    """Tests for list view on CurrencyViewSet."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: AnonymousUser as request.user.
        WHEN: CurrencyViewSet list endpoint called without authentication.
        THEN: HTTP 200 returned.
        """
        res = api_client.get(CURRENCIES_URL)

        assert res.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(self, api_client: APIClient):
        """
        GIVEN: Nine Currency model instances created in database during initial database migration.
        WHEN: CurrencyViewSet called without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        response = api_client.get(CURRENCIES_URL)

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 9

    def test_get_response_with_pagination(self, api_client: APIClient):
        """
        GIVEN: Nine Currency model instances created in database during initial database migration.
        WHEN: CurrencyViewSet called with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        response = api_client.get(CURRENCIES_URL, data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 9

    def test_retrieve_wallets_list(self, api_client: APIClient):
        """
        GIVEN: Nine Currency model instances created in database during initial database migration.
        WHEN: CurrencyViewSet called.
        THEN: HTTP 200. List of User Currencies returned.
        """
        response = api_client.get(CURRENCIES_URL)

        wallets = Currency.objects.all().order_by("name").distinct()
        serializer = CurrencySerializer(wallets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
