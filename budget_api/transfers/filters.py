from django_filters import rest_framework as filters
from transfers.models import TransferCategory


class TransferCategoriesFilterSet(filters.FilterSet):
    """FilterSet for /quests endpoint."""

    name = filters.CharFilter(lookup_expr='icontains', field_name='name')

    class Meta:
        model = TransferCategory
        fields = ['expense_group', 'income_group', 'owner', 'is_active']
