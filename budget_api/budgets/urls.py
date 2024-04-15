from budgets.views import BudgetingPeriodViewSet, BudgetViewSet
from deposits.views import DepositViewSet
from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter

app_name = 'budgets'


router = routers.DefaultRouter()
router.register(r'', BudgetViewSet)

budget_router = NestedSimpleRouter(router, r'', lookup='budget')
budget_router.register(r'periods', BudgetingPeriodViewSet, basename='period')
budget_router.register(r'deposits', DepositViewSet, basename='deposit')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(budget_router.urls)),
]
