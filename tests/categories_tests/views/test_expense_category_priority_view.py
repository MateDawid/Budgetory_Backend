import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.transfer_category_choices import ExpenseCategoryPriority

EXPENSE_CATEGORY_PRIORITY_URL = reverse("categories:expense-category-priorities")


@pytest.mark.django_db
class TestExpenseCategoryPriorityList:
    """Tests for list view on ExpenseCategoryViewSet."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: ExpenseCategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on EXPENSE_CATEGORY_PRIORITY_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(EXPENSE_CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_priorities_list(self, api_client: APIClient):
        """
        GIVEN: ExpenseCategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on EXPENSE_CATEGORY_PRIORITY_URL.
        THEN: HTTP_200_OK, choices for ExpenseCategoryPriority returned.
        """
        response = api_client.get(EXPENSE_CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [
            {"value": choice[0], "label": choice[1]} for choice in ExpenseCategoryPriority.choices
        ]
