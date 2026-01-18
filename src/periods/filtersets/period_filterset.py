from django_filters import rest_framework as filters

from periods.models.choices.period_status import PeriodStatus


class PeriodFilterSet(filters.FilterSet):
    """FilterSet for Period list endpoint."""

    name = filters.CharFilter(lookup_expr="icontains", field_name="name")
    date_start = filters.DateFromToRangeFilter()
    date_end = filters.DateFromToRangeFilter()
    status = filters.ChoiceFilter(choices=PeriodStatus.choices)
