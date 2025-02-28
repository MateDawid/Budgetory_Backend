import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.transfer_category_choices import IncomeCategoryPriority

INCOME_CATEGORY_PRIORITY_URL = reverse("categories:income-category-priorities")


@pytest.mark.django_db
class TestIncomeCategoryPriorityList:
    """Tests for list view on IncomeCategoryViewSet."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: IncomeCategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on EXPENSE_CATEGORY_PRIORITY_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(INCOME_CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_priorities_list(self, api_client: APIClient):
        """
        GIVEN: IncomeCategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on EXPENSE_CATEGORY_PRIORITY_URL.
        THEN: HTTP_200_OK, choices for IncomeCategoryPriority returned.
        """
        response = api_client.get(INCOME_CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [
            {"value": choice[0], "label": choice[1]} for choice in IncomeCategoryPriority.choices
        ]
