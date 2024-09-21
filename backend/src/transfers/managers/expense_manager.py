from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class ExpenseManager(models.Manager):
    """Manager for Transfers with ExpenseCategory as category."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only Transfers with ExpenseCategories as category.

        Returns:
            QuerySet: QuerySet containing only Transfers with ExpenseCategories as category.
        """
        return super().get_queryset().filter(category__category_type=CategoryType.EXPENSE)

    def create(self, *args, **kwargs) -> Model:
        """
        ???

        Returns:
            Model: Expense model instance.
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
