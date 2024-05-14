from django_filters import rest_framework as filters
from transfers.models import TransferCategory


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr='icontains', field_name='name')
    common_only = filters.BooleanFilter(method='get_common_categories')

    class Meta:
        abstract = True

    def get_common_categories(self, queryset, name, value):
        """
        Filtering QuerySet with objects containing .

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [Decimal]: Value of filtered param

        Returns:
            QuerySet: Input QuerySet filtered by filter param value.
        """
        if value:
            return queryset.filter(owner__isnull=True)
        return queryset


class ExpenseCategoryFilterSet(TransferCategoryFilterSet):
    """FilterSet for /expense_categories endpoint."""

    class Meta:
        model = TransferCategory
        fields = ['expense_group', 'owner', 'is_active']


class IncomeCategoryFilterSet(TransferCategoryFilterSet):
    """FilterSet for /income_categories endpoint."""

    class Meta:
        model = TransferCategory
        fields = ['income_group', 'owner', 'is_active']
