from django_filters import rest_framework as filters

from categories.models import ExpenseCategory
from transfers.filtersets.transfer_filterset import TransferFilterSet, get_budget_pk


class ExpenseFilterSet(TransferFilterSet):
    """FilterSet for /expense endpoint."""

    category = filters.ModelChoiceFilter(
        queryset=lambda request: ExpenseCategory.objects.filter(budget__pk=get_budget_pk(request))
    )
