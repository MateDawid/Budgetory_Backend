from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Model, QuerySet

from categories.models.transfer_category_choices import CategoryType


class IncomeQuerySet(QuerySet):
    """Custom IncomeQuerySet for validating input data for Income instances create and update."""

    def create(self, **kwargs) -> Model:
        """
        Method extended with additional check of "category" field.

        Returns:
            Model: Income model instance.

        Raises:
            ValidationError: Raised on category.category_type different from CategoryType.INCOME.
        """
        if not getattr(kwargs.get("category"), "category_type", None) == CategoryType.INCOME:
            raise ValidationError("Income model instance can not be created with ExpenseCategory.")
        return super().create(**kwargs)

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
    """Manager for Transfers with IncomeCategory as category."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only Transfers with IncomeCategories as category.

        Returns:
            QuerySet: QuerySet containing only Transfers with IncomeCategories as category.
        """
        return IncomeQuerySet(self.model, using=self._db).filter(category__category_type=CategoryType.INCOME)
