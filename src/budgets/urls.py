from django.urls import include, path

from app_infrastructure.routers import AppNestedRouter, AppRouter
from budgets.views.budget_viewset import BudgetViewSet
from budgets.views.budgeting_period_viewset import BudgetingPeriodViewSet
from budgets.views.period_status_view import PeriodStatusView
from categories.views.transfer_category_viewset import TransferCategoryViewSet
from entities.views.deposit_viewset import DepositViewSet
from entities.views.entity_viewset import EntityViewSet
from predictions.views.expense_prediction_viewset import ExpensePredictionViewSet
from transfers.views.expense_viewset import ExpenseViewSet
from transfers.views.income_viewset import IncomeViewSet

app_name = "budgets"

router = AppRouter()
router.register(r"", BudgetViewSet)

budget_router = AppNestedRouter(router, r"", lookup="budget")
budget_router.register(r"periods", BudgetingPeriodViewSet, basename="period")
budget_router.register(r"deposits", DepositViewSet, basename="deposit")
budget_router.register(r"entities", EntityViewSet, basename="entity")
budget_router.register(r"categories", TransferCategoryViewSet, basename="category")
budget_router.register(r"expense_predictions", ExpensePredictionViewSet, basename="expense_prediction")
budget_router.register(r"incomes", IncomeViewSet, basename="income")
budget_router.register(r"expenses", ExpenseViewSet, basename="expense")


urlpatterns = [
    path("", include(router.urls)),
    path("", include(budget_router.urls)),
    path("periods/statuses", PeriodStatusView.as_view(), name="period-status"),
]
