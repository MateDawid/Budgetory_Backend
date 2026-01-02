from decimal import Decimal

from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.request import Request

from budgets.utils import get_budget_pk
from entities.models import Deposit
from periods.models import BudgetingPeriod


class TransferFilterSet(filters.FilterSet):
    """Base FilterSet for Transfer endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    period = filters.ModelChoiceFilter(
        queryset=lambda request: BudgetingPeriod.objects.filter(budget__pk=get_budget_pk(request))
    )
    entity = filters.NumberFilter(method="filter_by_entity")
    deposit = filters.ModelChoiceFilter(
        queryset=lambda request: Deposit.objects.filter(budget__pk=get_budget_pk(request))
    )
    date = filters.DateFromToRangeFilter()
    value = filters.NumberFilter()
    value_min = filters.NumberFilter(field_name="value", lookup_expr="gte")
    value_max = filters.NumberFilter(field_name="value", lookup_expr="lte")

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

    def filter_by_entity(self, queryset: QuerySet, name: str, value: Decimal) -> QuerySet:
        """
        Filters Transfer queryset by Entity field value.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [Decimal]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        budget_pk = self.request.parser_context.get("kwargs", {}).get("budget_pk")
        if value == Decimal("-1"):
            return queryset.filter(period__budget__pk=budget_pk, entity__isnull=True)
        return queryset.filter(period__budget__pk=budget_pk, entity__id=value)
