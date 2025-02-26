from django.db import models


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    EXPENSE = 1, "Expense"
    INCOME = 2, "Income"


class ExpenseCategoryPriority(models.IntegerChoices):
    """
    Choices for ExpenseCategory priority value.
    """

    MOST_IMPORTANT = 101, "01. Most_important"
    DEBTS = 102, "02. Debts"
    SAVINGS = 103, "03. Savings"
    OTHERS = 104, "04. Others"


class IncomeCategoryPriority(models.IntegerChoices):
    """
    Choices for IncomeCategory priority value.
    """

    REGULAR = 201, "01. Regular"
    IRREGULAR = 202, "02. Irregular"
