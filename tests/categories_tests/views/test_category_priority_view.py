import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_priority import CategoryPriority

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
