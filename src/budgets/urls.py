from django.urls import include, path

from app_infrastructure.routers import AppNestedRouter, AppRouter
from budgets.views.budget_viewset import BudgetViewSet
from budgets.views.budgeting_period_viewset import BudgetingPeriodViewSet
from categories.views.expense_category_viewset import ExpenseCategoryViewSet
from categories.views.income_category_viewset import IncomeCategoryViewSet
from entities.views.deposit_viewset import DepositViewSet
from entities.views.entity_viewset import EntityViewSet
from predictions.views.expense_prediction_viewset import ExpensePredictionViewSet
from transfers.views.expense_viewset import ExpenseViewSet
from transfers.views.income_viewset import IncomeViewSet
from wallets.views.wallet_viewset import WalletViewSet

app_name = "budgets"

router = AppRouter()
router.register(r"", BudgetViewSet)

budget_router = AppNestedRouter(router, r"", lookup="budget")
budget_router.register(r"periods", BudgetingPeriodViewSet, basename="period")
budget_router.register(r"deposits", DepositViewSet, basename="deposit")
budget_router.register(r"entities", EntityViewSet, basename="entity")
budget_router.register(r"income_categories", IncomeCategoryViewSet, basename="income_category")
budget_router.register(r"expense_categories", ExpenseCategoryViewSet, basename="expense_category")
budget_router.register(r"expense_predictions", ExpensePredictionViewSet, basename="expense_prediction")
budget_router.register(r"incomes", IncomeViewSet, basename="income")
budget_router.register(r"expenses", ExpenseViewSet, basename="expense")
budget_router.register(r"wallets", WalletViewSet, basename="wallet")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(budget_router.urls)),
]
