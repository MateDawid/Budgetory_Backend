import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_type import CategoryType

CATEGORY_TYPE_URL = reverse("categories:category-type")


@pytest.mark.django_db
class TestCategoryTypeView:
    """Tests for list view on CategoryTypeView."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: CategoryType choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_TYPE_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(CATEGORY_TYPE_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_category_type_list(self, api_client: APIClient):
        """
        GIVEN: CategoryType choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_TYPE_URL.
        THEN: HTTP_200_OK, choices for CategoryType returned.
        """
        response = api_client.get(CATEGORY_TYPE_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [{"value": choice[0], "label": choice[1]} for choice in CategoryType.choices]
