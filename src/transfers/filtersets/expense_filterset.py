from django_filters import rest_framework as filters

from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from transfers.filtersets.transfer_filterset import TransferFilterSet, get_budget_pk


class ExpenseFilterSet(TransferFilterSet):
    """FilterSet for /expense endpoint."""

    category = filters.ModelChoiceFilter(
        queryset=lambda request: TransferCategory.objects.filter(
            budget__pk=get_budget_pk(request), category_type=CategoryType.EXPENSE
        )
    )
