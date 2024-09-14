from django_filters import rest_framework as filters

from categories.filters.transfer_category_filterset import TransferCategoryFilterSet
from categories.models.transfer_category_choices import ExpenseCategoryPriority


class ExpenseCategoryFilterSet(TransferCategoryFilterSet):
    """FilterSet for /expense_categories endpoint."""

    priority = filters.ChoiceFilter(choices=ExpenseCategoryPriority.choices)
