from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class IncomeCategoryManager(models.Manager):
    """Manager for INCOME type TransferCategories."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only TransferCategories with INCOME category_type.

        Returns:
            QuerySet: QuerySet containing only TransferCategories with INCOME category_type.
        """
        return super().get_queryset().filter(category_type=CategoryType.INCOME)

    def create(self, *args, **kwargs) -> Model:
        """
        Sets category_type value to INCOME before instance creation.

        Returns:
            Model: Deposit model instance.
        """
        kwargs["category_type"] = CategoryType.INCOME
        return super().create(*args, **kwargs)

    def update(self, *args, **kwargs) -> int:
        """
        Sets category_type value to INCOME before instance update.

        Returns:
            int: Number of affected database rows.
        """
        kwargs["category_type"] = CategoryType.INCOME
        return super().update(*args, **kwargs)
