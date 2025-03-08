from django.core.exceptions import ValidationError

from categories.models.choices.category_type import CategoryType
from transfers.managers.income_manager import IncomeManager
from transfers.models.transfer_model import Transfer


class Income(Transfer):
    """Income proxy model for Transfer with IncomeCategory as category."""

    objects = IncomeManager()

    class Meta:
        proxy = True
        verbose_name_plural = "incomes"

    def save(self, *args, **kwargs) -> None:
        if not self.category.category_type == CategoryType.INCOME:
            raise ValidationError("Income model instance can not be created with ExpenseCategory.")
        super().save(*args, **kwargs)
