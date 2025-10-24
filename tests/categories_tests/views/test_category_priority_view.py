import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.views.category_priority_view import format_typed_priorities

CATEGORY_PRIORITY_URL = reverse("categories:category-priority")


@pytest.mark.django_db
class TestCategoryPriorityView:
    """Tests for list view on CategoryPriorityView."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: CategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_PRIORITY_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_priorities_list(self, api_client: APIClient):
        """
        GIVEN: CategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_PRIORITY_URL.
        THEN: HTTP_200_OK, choices for CategoryPriority returned.
        """
        response = api_client.get(CATEGORY_PRIORITY_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [
            {"value": choice[0], "label": choice[1]} for choice in CategoryPriority.choices
        ]

    def test_get_priorities_list_filtered_with_income(self, api_client: APIClient):
        """
        GIVEN: CategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_PRIORITY_URL with INCOME type filter.
        THEN: HTTP_200_OK, choices for CategoryPriority returned.
        """
        response = api_client.get(CATEGORY_PRIORITY_URL, data={"type": CategoryType.INCOME.value})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [
            {"value": choice[0], "label": choice[1]}
            for choice in format_typed_priorities(CategoryPriority.income_priorities())
        ]

    def test_get_priorities_list_filtered_with_expense(self, api_client: APIClient):
        """
        GIVEN: CategoryPriority choices defined in application.
        WHEN: Performing HTTP GET request on CATEGORY_PRIORITY_URL with EXPENSE type filter.
        THEN: HTTP_200_OK, choices for CategoryPriority returned.
        """
        response = api_client.get(CATEGORY_PRIORITY_URL, data={"type": CategoryType.EXPENSE.value})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [
            {"value": choice[0], "label": choice[1]}
            for choice in format_typed_priorities(CategoryPriority.expense_priorities())
        ]
