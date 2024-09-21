from transfers.managers.income_manager import IncomeManager
from transfers.models.transfer_model import Transfer


class Income(Transfer):
    """Income proxy model for Transfer with IncomeCategory as category."""

    objects = IncomeManager()

    class Meta:
        proxy = True
        verbose_name_plural = "incomes"
