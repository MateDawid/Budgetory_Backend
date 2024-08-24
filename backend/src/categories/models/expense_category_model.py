from categories.managers.expense_category_manager import ExpenseCategoryManager
from categories.models.category_type_choices import CategoryType
from categories.models.transfer_category_model import TransferCategory


class ExpenseCategory(TransferCategory):
    """ExpenseCategory proxy model for TransferCategory with type EXPENSE."""

    objects = ExpenseCategoryManager()

    class Meta:
        proxy = True
        verbose_name_plural = "expense categories"

    def __init__(self, *args, **kwargs) -> None:
        """
        Magic __init__ method extended with setting EXPENSE value for category_type value.
        """
        super().__init__(*args, **kwargs)
        setattr(self, "category_type", CategoryType.EXPENSE)
