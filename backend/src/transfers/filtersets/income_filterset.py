from django_filters import rest_framework as filters

from categories.models.income_category_model import IncomeCategory
from transfers.filtersets.transfer_filterset import TransferFilterSet, get_budget_pk


class IncomeFilterSet(TransferFilterSet):
    """FilterSet for /income endpoint."""

    category = filters.ModelChoiceFilter(
        queryset=lambda request: IncomeCategory.objects.filter(budget__pk=get_budget_pk(request))
    )
