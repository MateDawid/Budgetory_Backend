from django.urls import path

from predictions.views.users_results_viewset import UsersResultsAPIView

app_name = "predictions"

urlpatterns = [
    path("", UsersResultsAPIView.as_view(), name="users-results"),
]
