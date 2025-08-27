from django_filters import rest_framework as filters
from rest_framework.request import Request

from budgets.models import BudgetingPeriod
from budgets.utils import get_budget_pk
from categories.models import TransferCategory
from entities.models import Deposit, Entity


class TransferFilterSet(filters.FilterSet):
    """Base FilterSet for Transfer endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    period = filters.ModelChoiceFilter(
        queryset=lambda request: BudgetingPeriod.objects.filter(budget__pk=get_budget_pk(request))
    )
    entity = filters.ModelChoiceFilter(
        queryset=lambda request: Entity.objects.filter(budget__pk=get_budget_pk(request))
    )
    deposit = filters.ModelChoiceFilter(
        queryset=lambda request: Deposit.objects.filter(budget__pk=get_budget_pk(request))
    )
    category = filters.ModelChoiceFilter(
        queryset=lambda request: TransferCategory.objects.filter(budget__pk=get_budget_pk(request))
    )
    date = filters.DateFromToRangeFilter()
    value = filters.NumberFilter()
    value_min = filters.NumberFilter(field_name="value", lookup_expr="gte")
    value_max = filters.NumberFilter(field_name="value", lookup_expr="lte")
    deposit_transfers_only = filters.BooleanFilter(field_name="entity__is_deposit", lookup_expr="exact")

    @staticmethod
    def get_budget_pk(request: Request) -> int:
        """
        Retrieves Budget PK from User Request.

        Args:
            request (Request): User request.

        Returns:
            int: Budget PK.
        """
        return request.parser_context.get("kwargs", {}).get("budget_pk")  # pragma: no cover
