from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class ExpenseCategoryQuerySet(QuerySet):
    """Custom ExpenseCategoryQuerySet for handling ExpenseCategory model QuerySets."""

    def create(self, **kwargs) -> Model:
        """
        Sets category_type value to EXPENSE before instance creation.

        Returns:
            Model: Expense model instance.
        """
        kwargs["category_type"] = CategoryType.EXPENSE
        return super().create(**kwargs)

    def update(self, **kwargs) -> int:
        """
        Sets category_type value to EXPENSE before instance update.

        Returns:
            int: Number of affected database rows.
        """
        kwargs["category_type"] = CategoryType.EXPENSE
        return super().update(**kwargs)


class ExpenseCategoryManager(models.Manager):
    """Manager for EXPENSE type TransferCategories."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only TransferCategories with EXPENSE category_type.

        Returns:
            QuerySet: QuerySet containing only TransferCategories with EXPENSE category_type.
        """
        return ExpenseCategoryQuerySet(self.model, using=self._db).filter(category_type=CategoryType.EXPENSE)
