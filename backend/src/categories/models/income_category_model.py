from categories.managers.income_category_manager import IncomeCategoryManager
from categories.models.category_type_choices import CategoryType
from categories.models.transfer_category_model import TransferCategory


class IncomeCategory(TransferCategory):
    """IncomeCategory proxy model for TransferCategory with type INCOME."""

    objects = IncomeCategoryManager()

    class Meta:
        proxy = True
        verbose_name_plural = "income categories"

    def save(self, *args, **kwargs) -> None:
        """
        Overridden save method to make sure, that category_type is always CategoryType.INCOME.
        """
        self.category_type = CategoryType.INCOME
        super().save(*args, **kwargs)
