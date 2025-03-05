from django.db.models import QuerySet
from django_filters import rest_framework as filters


class TransferCategoryFilterSet(filters.FilterSet):
    """Base FilterSet for TransferCategory endpoints."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    owner = filters.NumberFilter(method="get_owner")
    is_active = filters.BooleanFilter(field_name="is_active")
    description = filters.CharFilter(lookup_expr="icontains", field_name="description")

    @staticmethod
    def get_owner(queryset: QuerySet, name: str, value: str) -> QuerySet:
        """
        Filters TransferCategories queryset by owner field value.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [str]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        if value == -1:
            return queryset.filter(owner__isnull=True)
        return queryset.filter(owner__id=value)
