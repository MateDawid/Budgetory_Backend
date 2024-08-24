from categories.managers.income_category_manager import IncomeCategoryManager
from categories.models.category_type_choices import CategoryType
from categories.models.transfer_category_model import TransferCategory


class IncomeCategory(TransferCategory):
    """IncomeCategory proxy model for TransferCategory with type INCOME."""

    category_type = CategoryType.INCOME
    objects = IncomeCategoryManager()

    class Meta:
        proxy = True
        verbose_name_plural = "income categories"

    def __init__(self, *args, **kwargs) -> None:
        """
        Magic __init__ method extended with setting INCOME value for category_type value.
        """
        super().__init__(*args, **kwargs)
        setattr(self, "category_type", CategoryType.INCOME)
