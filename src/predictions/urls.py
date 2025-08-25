from django.urls import path

from predictions.views.copy_predictions_from_previous_period_view import CopyPredictionsFromPreviousPeriodAPIView
from predictions.views.users_results_view import UsersResultsAPIView

app_name = "predictions"

urlpatterns = [
    path("user_results/<int:period_pk>/", UsersResultsAPIView.as_view(), name="users-results"),
    path(
        "copy_predictions_from_previous_period/<int:period_pk>/",
        CopyPredictionsFromPreviousPeriodAPIView.as_view(),
        name="copy-predictions-from-previous-period",
    ),
]
