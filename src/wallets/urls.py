from django.urls import include, path

from app_infrastructure.routers import AppNestedRouter, AppRouter
from categories.views.transfer_category_viewset import TransferCategoryViewSet
from entities.views.deposit_viewset import DepositViewSet
from entities.views.entity_viewset import EntityViewSet
from periods.views.period_status_view import PeriodStatusView
from periods.views.period_viewset import PeriodViewSet
from predictions.views.expense_prediction_viewset import ExpensePredictionViewSet
from transfers.views.expense_viewset import ExpenseViewSet
from transfers.views.income_viewset import IncomeViewSet
from wallets.views.wallet_viewset import WalletViewSet

app_name = "wallets"

router = AppRouter()
router.register(r"", WalletViewSet)

wallet_router = AppNestedRouter(router, r"", lookup="wallet")
wallet_router.register(r"periods", PeriodViewSet, basename="period")
wallet_router.register(r"deposits", DepositViewSet, basename="deposit")
wallet_router.register(r"entities", EntityViewSet, basename="entity")
wallet_router.register(r"categories", TransferCategoryViewSet, basename="category")
wallet_router.register(r"expense_predictions", ExpensePredictionViewSet, basename="expense_prediction")
wallet_router.register(r"incomes", IncomeViewSet, basename="income")
wallet_router.register(r"expenses", ExpenseViewSet, basename="expense")


urlpatterns = [
    path("", include(router.urls)),
    path("", include(wallet_router.urls)),
    path("periods/statuses", PeriodStatusView.as_view(), name="period-status"),
]
