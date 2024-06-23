from categories.models import ExpenseCategory, IncomeCategory
from django_filters import rest_framework as filters


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr='icontains', field_name='name')
    common_only = filters.BooleanFilter(method='get_common_categories')

    class Meta:
        abstract = True
        fields = ['group', 'owner', 'is_active']

    def get_common_categories(self, queryset, name, value):
        """
        Filtering QuerySet TransferCategories with or without owner.

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

    class Meta(TransferCategoryFilterSet.Meta):
        model = ExpenseCategory


class IncomeCategoryFilterSet(TransferCategoryFilterSet):
    """FilterSet for /income_categories endpoint."""

    class Meta(TransferCategoryFilterSet.Meta):
        model = IncomeCategory
