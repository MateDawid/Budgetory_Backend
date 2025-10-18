from django_filters import rest_framework as filters

from budgets.utils import get_budget_pk
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    description = filters.CharFilter(lookup_expr="icontains", field_name="description")
    deposit = filters.ModelChoiceFilter(
        queryset=lambda request: Deposit.objects.filter(budget__pk=get_budget_pk(request))
    )
    is_active = filters.BooleanFilter(field_name="is_active")
    category_type = filters.ChoiceFilter(choices=CategoryType.choices)
    priority = filters.ChoiceFilter(choices=CategoryPriority.choices)
