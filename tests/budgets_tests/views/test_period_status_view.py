import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models.choices.period_status import PeriodStatus

PERIOD_STATUS_URL = reverse("budgets:period-status")


@pytest.mark.django_db
class TestPeriodStatusView:
    """Tests for list view on PeriodStatusView."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: PeriodStatus choices defined in application.
        WHEN: Performing HTTP GET request on PERIOD_STATUS_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(PERIOD_STATUS_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_period_status_list(self, api_client: APIClient):
        """
        GIVEN: PeriodStatus choices defined in application.
        WHEN: Performing HTTP GET request on PERIOD_STATUS_URL.
        THEN: HTTP_200_OK, choices for PeriodStatus returned.
        """
        response = api_client.get(PERIOD_STATUS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == [{"value": choice[0], "label": choice[1]} for choice in PeriodStatus.choices]
