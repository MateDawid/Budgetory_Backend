from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import QuerySet

from categories.models.choices.category_type import CategoryType


class ExpenseQuerySet(QuerySet):
    """Custom ExpenseQuerySet for validating input data for Expense instances create and update."""

    def update(self, **kwargs) -> int:
        """
        Method extended with additional check of "category" field.

        Returns:
            int: Number of affected database rows.

        Raises:
            ValidationError: Raised on category.category_type different from CategoryType.EXPENSE.
        """
        if "category" in kwargs and kwargs["category"].category_type != CategoryType.EXPENSE:
            raise ValidationError("Expense model instance can not be created with IncomeCategory.")
        return super().update(**kwargs)


class ExpenseManager(models.Manager):
    """Manager for Transfers with ExpenseCategory as category."""

    def get_queryset(self) -> QuerySet:
        """
        Returns only Transfers with ExpenseCategories as category.

        Returns:
            QuerySet: QuerySet containing only Transfers with ExpenseCategories as category.
        """
        return ExpenseQuerySet(self.model, using=self._db).filter(category__category_type=CategoryType.EXPENSE)
