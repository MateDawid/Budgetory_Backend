from django.db import models
from django.db.models import Model, QuerySet

from categories.models.category_type_choices import CategoryType


class ExpenseCategoryManager(models.Manager):
    """Manager for EXPENSE type TransferCategories."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only TransferCategories with EXPENSE category_type.

        Returns:
            QuerySet: QuerySet containing only TransferCategories with EXPENSE category_type.
        """
        return super().get_queryset().filter(category_type=CategoryType.EXPENSE)

    def create(self, *args, **kwargs) -> Model:
        """
        Sets category_type value to EXPENSE before instance creation.

        Returns:
            Model: Deposit model instance.
        """
        kwargs["category_type"] = CategoryType.EXPENSE
        return super().create(*args, **kwargs)

    def update(self, *args, **kwargs) -> int:
        """
        Sets category_type value to EXPENSE before instance update.

        Returns:
            int: Number of affected database rows.
        """
        kwargs["category_type"] = CategoryType.EXPENSE
        return super().update(**kwargs)
