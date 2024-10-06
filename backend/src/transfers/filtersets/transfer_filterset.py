from django.db.models import QuerySet
from django_filters import rest_framework as filters

from budgets.models import BudgetingPeriod
from categories.models import TransferCategory
from entities.models import Deposit, Entity


def get_budget_pk(request):
    return request.parser_context.get("kwargs", {}).get("budget_pk")


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
    owner = filters.NumberFilter(method="get_owner_transfers")
    common_only = filters.BooleanFilter(method="get_common_transfers")
    date = filters.DateFromToRangeFilter()
    value = filters.NumericRangeFilter()

    @staticmethod
    def get_budget_pk(request):
        return request.parser_context.get("kwargs", {}).get("budget_pk")

    @staticmethod
    def get_owner_transfers(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filtering QuerySet Transfer with given category owner.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [str]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        return queryset.filter(category__owner__pk=value)

    @staticmethod
    def get_common_transfers(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filtering QuerySet Transfer with category with or without an owner.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [str]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        if value is True:
            return queryset.filter(category__owner__isnull=True)
        return queryset  # pragma: no cover
