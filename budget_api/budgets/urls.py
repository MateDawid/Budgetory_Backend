from budgets.views import BudgetingPeriodViewSet, BudgetViewSet
from deposits.views import DepositViewSet
from django.urls import include, path
from rest_framework import routers
from rest_framework_nested.routers import NestedSimpleRouter
from transfers.views.transfer_category_group_view import TransferCategoryGroupViewSet

app_name = 'budgets'


router = routers.DefaultRouter()
router.register(r'', BudgetViewSet)

budget_router = NestedSimpleRouter(router, r'', lookup='budget')
budget_router.register(r'periods', BudgetingPeriodViewSet, basename='period')
budget_router.register(r'deposits', DepositViewSet, basename='deposit')
budget_router.register(r'category_groups', TransferCategoryGroupViewSet, basename='category_group')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(budget_router.urls)),
]
