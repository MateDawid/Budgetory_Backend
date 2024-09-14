from django.db.models import QuerySet
from django_filters import rest_framework as filters


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    common_only = filters.BooleanFilter(method="get_common_categories")
    owner = filters.NumberFilter(field_name="owner")
    is_active = filters.BooleanFilter(field_name="is_active")

    @staticmethod
    def get_common_categories(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filtering QuerySet TransferCategories with or without owner.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [str]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        if value is True:
            return queryset.filter(owner__isnull=True)
        return queryset
