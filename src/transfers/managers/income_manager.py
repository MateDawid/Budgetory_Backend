from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet

from categories.models.choices.category_type import CategoryType


class IncomeQuerySet(QuerySet):
    """Custom IncomeQuerySet for validating input data for Income instances create and update."""

    def update(self, **kwargs) -> int:
        """
        Method extended with additional check of "category" field.

        Returns:
            int: Number of affected database rows.

        Raises:
            ValidationError: Raised on category.category_type different from CategoryType.INCOME.
        """
        if "category" in kwargs and kwargs["category"].category_type != CategoryType.INCOME:
            raise ValidationError("Income model instance can not be created with ExpenseCategory.")
        return super().update(**kwargs)


class IncomeManager(models.Manager):
    """Manager for Income Transfers."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only Income Transfers.

        Returns:
            QuerySet: QuerySet containing only Income type Transfers.
        """
        return IncomeQuerySet(self.model, using=self._db).filter(transfer_type=CategoryType.INCOME)
