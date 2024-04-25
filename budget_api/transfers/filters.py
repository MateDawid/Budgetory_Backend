from django_filters import rest_framework as filters
from transfers.models.transfer_category_model import TransferCategory


class TransferCategoriesFilterSet(filters.FilterSet):
    """FilterSet for /quests endpoint."""

    name = filters.CharFilter(lookup_expr='icontains', field_name='name')

    class Meta:
        model = TransferCategory
        fields = ['group', 'owner', 'is_active']
