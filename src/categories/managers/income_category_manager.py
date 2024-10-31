from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class IncomeCategoryQuerySet(QuerySet):
    """Custom IncomeCategoryQuerySet for handling IncomeCategory model QuerySets."""

    def create(self, *args, **kwargs) -> Model:
        """
        Sets category_type value to INCOME before instance creation.

        Returns:
            Model: IncomeCategory model instance.
        """
        kwargs["category_type"] = CategoryType.INCOME
        return super().create(**kwargs)

    def update(self, *args, **kwargs) -> int:
        """
        Sets category_type value to INCOME before instance update.

        Returns:
            int: Number of affected database rows.
        """
        kwargs["category_type"] = CategoryType.INCOME
        return super().update(**kwargs)


class IncomeCategoryManager(models.Manager):
    """Manager for INCOME type TransferCategories."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only TransferCategories with INCOME category_type.

        Returns:
            QuerySet: QuerySet containing only TransferCategories with INCOME category_type.
        """
        return IncomeCategoryQuerySet(self.model, using=self._db).filter(category_type=CategoryType.INCOME)
