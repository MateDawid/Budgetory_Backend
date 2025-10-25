from django.urls import path

from predictions.views.copy_predictions_from_previous_period_view import CopyPredictionsFromPreviousPeriodAPIView
from predictions.views.deposits_predictions_results_view import DepositsPredictionsResultsAPIView

app_name = "predictions"

urlpatterns = [
    path(
        "deposits_predictions_results/<int:period_pk>/",
        DepositsPredictionsResultsAPIView.as_view(),
        name="deposits-predictions-results",
    ),
    path(
        "copy_predictions_from_previous_period/<int:period_pk>/",
        CopyPredictionsFromPreviousPeriodAPIView.as_view(),
        name="copy-predictions-from-previous-period",
    ),
]
