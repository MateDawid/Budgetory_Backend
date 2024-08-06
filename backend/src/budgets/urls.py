from app_infrastructure.routers import AppRouter
from budgets.views.budget_viewset import BudgetViewSet
from budgets.views.budgeting_period_viewset import BudgetingPeriodViewSet
from categories.views import ExpenseCategoryViewSet, IncomeCategoryViewSet
from django.urls import include, path
from entities.views.deposit_viewset import DepositViewSet
from entities.views.entity_viewset import EntityViewSet
from predictions.views import ExpensePredictionViewSet
from rest_framework_nested.routers import NestedSimpleRouter

app_name = 'budgets'

router = AppRouter()
router.register(r'', BudgetViewSet)

budget_router = NestedSimpleRouter(router, r'', lookup='budget')
budget_router.register(r'periods', BudgetingPeriodViewSet, basename='period')
budget_router.register(r'deposits', DepositViewSet, basename='deposit')
budget_router.register(r'entities', EntityViewSet, basename='entity')
budget_router.register(r'income_categories', IncomeCategoryViewSet, basename='income_category')
budget_router.register(r'expense_categories', ExpenseCategoryViewSet, basename='expense_category')
budget_router.register(r'expense_predictions', ExpensePredictionViewSet, basename='expense_prediction')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(budget_router.urls)),
]
