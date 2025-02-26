from django_filters import rest_framework as filters


class BudgetFilterSet(filters.FilterSet):
    """FilterSet for Budget list endpoint."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
