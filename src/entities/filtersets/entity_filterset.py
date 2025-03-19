from django_filters import rest_framework as filters

from entities.filtersets.deposit_filterset import DepositFilterSet


class EntityFilterSet(DepositFilterSet):
    """FilterSet for Entity endpoint."""

    is_deposit = filters.BooleanFilter(field_name="is_deposit")
