from django_filters import rest_framework as filters

from categories.filtersets.transfer_category_filterset import TransferCategoryFilterSet
from categories.models.transfer_category_choices import IncomeCategoryPriority


class IncomeCategoryFilterSet(TransferCategoryFilterSet):
    """FilterSet for /income_categories endpoint."""

    priority = filters.ChoiceFilter(choices=IncomeCategoryPriority.choices)
