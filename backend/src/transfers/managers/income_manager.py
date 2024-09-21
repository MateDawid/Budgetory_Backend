from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class IncomeManager(models.Manager):
    """Manager for Transfers with IncomeCategory as category."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only Transfers with IncomeCategories as category.

        Returns:
            QuerySet: QuerySet containing only Transfers with IncomeCategories as category.
        """
        return super().get_queryset().filter(category__category_type=CategoryType.INCOME)

    def create(self, *args, **kwargs) -> Model:
        """
        ???

        Returns:
            Model: Income model instance.
        """
        _ = ""
        return super().create(*args, **kwargs)

    def update(self, *args, **kwargs) -> int:
        """
        ???

        Returns:
            int: Number of affected database rows.
        """
        _ = ""
        return super().update(**kwargs)
