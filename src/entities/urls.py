from django.urls import path

from entities.views.deposit_type_view import DepositTypeView
from entities.views.deposits_results_view import DepositsResultsAPIView

app_name = "entities"

urlpatterns = [
    path("entities/deposit_types/", DepositTypeView.as_view(), name="deposit-types"),
    path("budgets/<int:budget_pk>/deposits_results/", DepositsResultsAPIView.as_view(), name="deposits-results"),
]
