from django.db import models


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    EXPENSE = 1, "Expense"
    INCOME = 2, "Income"
