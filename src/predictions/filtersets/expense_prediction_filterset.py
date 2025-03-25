from django_filters import rest_framework as filters

from budgets.models import BudgetingPeriod
from budgets.utils import get_budget_pk
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType


class ExpensePredictionFilterSet(filters.FilterSet):
    """FilterSet for ExpensePrediction endpoints."""

    period = filters.ModelChoiceFilter(
        queryset=lambda request: BudgetingPeriod.objects.filter(budget__pk=get_budget_pk(request))
    )
    category = filters.ModelChoiceFilter(
        queryset=lambda request: TransferCategory.objects.filter(
            budget__pk=get_budget_pk(request), category_type=CategoryType.EXPENSE
        )
    )
    initial_value = filters.NumericRangeFilter()
    current_value = filters.NumericRangeFilter()
