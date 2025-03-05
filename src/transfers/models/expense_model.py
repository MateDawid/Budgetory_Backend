from django.core.exceptions import ValidationError

from categories.models.choices.category_type import CategoryType
from transfers.managers.expense_manager import ExpenseManager
from transfers.models.transfer_model import Transfer


class Expense(Transfer):
    """Expense proxy model for Transfer with ExpenseCategory as category."""

    objects = ExpenseManager()

    class Meta:
        proxy = True
        verbose_name_plural = "expenses"

    def save(self, *args, **kwargs) -> None:
        if not self.category.category_type == CategoryType.EXPENSE:
            raise ValidationError("Expense model instance can not be created with IncomeCategory.")
        super().save(*args, **kwargs)
