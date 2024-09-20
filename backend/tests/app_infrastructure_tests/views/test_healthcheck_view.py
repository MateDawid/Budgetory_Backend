from unittest.mock import MagicMock, patch

import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@patch("app_infrastructure.services.database_connection_service.DatabaseConnectionService.is_connection_alive")
class TestHealthcheckView:
    """Tests for HealthcheckView."""

    url = reverse("healthcheck")

    def test_database_connection_alive(self, patched_check_connection: MagicMock, api_client: APIClient):
        """
        GIVEN: Database connection ongoing.
        WHEN: Calling HealthcheckView with GET.
        THEN: HTTP 200 returned.
        """
        patched_check_connection.return_value = True

        response = api_client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    @patch("os.kill")
    def test_database_connection_dead(
        self, patched_os_kill: MagicMock, patched_check_connection: MagicMock, api_client: APIClient
    ):
        """
        GIVEN: Database connection broken.
        WHEN: Calling HealthcheckView with GET.
        THEN: App pod killed with os.kill().
        """
        patched_check_connection.return_value = False
        patched_os_kill.side_effect = [HttpResponse]

        # ValueError appears only in test, due to mocking os.kill() as DRF awaiting HttpResponse returned.
        # In app, after os.kill() call pod will be killed and ValueError won't be raised.
        with pytest.raises(ValueError) as exc:
            api_client.get(self.url)
        assert patched_os_kill.call_count == 1
        assert str(exc.value) == (
            "The view app_infrastructure.views.healthcheck_view.view didn't return an "
            "HttpResponse object. It returned None instead."
        )
