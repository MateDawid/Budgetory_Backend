from django.db import models


class CategoryPriority(models.IntegerChoices):
    """
    Choices for TransferCategory priority value.

    Value 0 (INCOMES) dedicated for CategoryType.INCOME.
    Values 1-4 dedicated for CategoryType.EXPENSE.
    """

    INCOMES = 0, "Incomes"
    MOST_IMPORTANT = 1, "Most important"
    DEBTS = 2, "Debts"
    SAVINGS = 3, "Savings"
    OTHERS = 4, "Others"
