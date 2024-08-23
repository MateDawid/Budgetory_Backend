from categories.managers.expense_category_manager import ExpenseCategoryManager
from categories.models.category_type_choices import CategoryType
from categories.models.transfer_category_model import TransferCategory


class ExpenseCategory(TransferCategory):
    """ExpenseCategory proxy model for TransferCategory with type EXPENSE."""

    objects = ExpenseCategoryManager()

    class Meta:
        proxy = True
        verbose_name_plural = "expense categories"

    def save(self, *args, **kwargs) -> None:
        """
        Overridden save method to make sure, that category_type is always CategoryType.INCOME.
        """
        self.category_type = CategoryType.EXPENSE
        super().save(*args, **kwargs)
