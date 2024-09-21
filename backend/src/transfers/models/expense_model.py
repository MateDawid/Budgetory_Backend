from transfers.models.transfer_model import Transfer


class Expense(Transfer):
    """Expense proxy model for Transfer with ExpenseCategory as category."""

    # objects = ExpenseManager()

    class Meta:
        proxy = True
        verbose_name_plural = "expenses"
