from django.db import models


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    INCOME = 0, "Income"
    EXPENSE = 1, "Expense"
