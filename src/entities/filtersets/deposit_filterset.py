from django_filters import rest_framework as filters

from entities.models.choices.deposit_type import DepositType


class DepositFilterSet(filters.FilterSet):
    """FilterSet for Deposit endpoint."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    description = filters.CharFilter(lookup_expr="icontains", field_name="description")
    is_active = filters.BooleanFilter(field_name="is_active")
    balance = filters.NumberFilter()
    balance_min = filters.NumberFilter(field_name="balance", lookup_expr="gte")
    balance_max = filters.NumberFilter(field_name="balance", lookup_expr="lte")
    deposit_type = filters.ChoiceFilter(choices=DepositType.choices)
