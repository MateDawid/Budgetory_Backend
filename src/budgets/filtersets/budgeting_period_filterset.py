from django_filters import rest_framework as filters


class BudgetingPeriodFilterSet(filters.FilterSet):
    """FilterSet for BudgetingPeriod list endpoint."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    date_start = filters.DateFromToRangeFilter()
    date_end = filters.DateFromToRangeFilter()
    is_active = filters.BooleanFilter()
