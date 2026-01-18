from django_filters import rest_framework as filters

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from wallets.utils import get_wallet_pk


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    description = filters.CharFilter(lookup_expr="icontains", field_name="description")
    deposit = filters.ModelChoiceFilter(
        queryset=lambda request: Deposit.objects.filter(wallet__pk=get_wallet_pk(request))
    )
    is_active = filters.BooleanFilter(field_name="is_active")
    category_type = filters.ChoiceFilter(choices=CategoryType.choices)
    priority = filters.ChoiceFilter(choices=CategoryPriority.choices)
