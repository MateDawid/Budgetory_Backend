from decimal import Decimal

from django.db.models import QuerySet
from django_filters import rest_framework as filters

from categories.models.choices.category_type import CategoryType
from transfers.filtersets.transfer_filterset import TransferFilterSet


class ExpenseFilterSet(TransferFilterSet):
    """FilterSet for /expense endpoint."""

    category = filters.NumberFilter(method="filter_by_category")

    def filter_by_category(self, queryset: QuerySet, name: str, value: Decimal) -> QuerySet:
        """
        Filters Transfer queryset by TransferCategory field value.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [Decimal]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        wallet_pk = self.request.parser_context.get("kwargs", {}).get("wallet_pk")
        if value == Decimal("-1"):
            return queryset.filter(period__wallet__pk=wallet_pk, category__isnull=True)
        return queryset.filter(
            period__wallet__pk=wallet_pk, category__id=value, category__category_type=CategoryType.EXPENSE
        )
