import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from predictions.views.prediction_progress_status_view import PredictionProgressStatus

PREDICTIONS_PROGRESS_STATUS_URL = reverse("prediction-progress-status")


@pytest.mark.django_db
class TestPredictionProgressStatusView:
    """Tests for list view on PredictionProgressStatusView."""

    def test_auth_not_required(self, api_client: APIClient):
        """
        GIVEN: PredictionProgressStatus choices defined in application.
        WHEN: Performing HTTP GET request on PREDICTIONS_PROGRESS_STATUS_URL without authentication.
        THEN: HTTP_200_OK returned, endpoint accessible without authentication.
        """
        response = api_client.get(PREDICTIONS_PROGRESS_STATUS_URL)

        assert response.status_code == status.HTTP_200_OK

    def test_get_choices_list(self, api_client: APIClient):
        """
        GIVEN: PredictionProgressStatus choices defined in application.
        WHEN: Performing HTTP GET request on PREDICTIONS_PROGRESS_STATUS_URL.
        THEN: HTTP_200_OK, choices for PredictionProgressStatus returned.
        """
        response = api_client.get(PREDICTIONS_PROGRESS_STATUS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == PredictionProgressStatus.choices()
