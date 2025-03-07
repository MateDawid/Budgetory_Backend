from django.db import models


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    INCOME = 1, "📈 Income"
    EXPENSE = 2, "📉 Expense"
