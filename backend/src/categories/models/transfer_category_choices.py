from django.db import models


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    EXPENSE = 1, "Expense"
    INCOME = 2, "Income"


class ExpenseCategoryPriority(models.IntegerChoices):
    """
    Choices for ExpenseCategory priority value.
    """

    MOST_IMPORTANT = 101, "EXPENSE_Most_important"
    DEBTS = 102, "EXPENSE_Debts"
    SAVINGS = 103, "EXPENSE_Savings"
    OTHERS = 104, "EXPENSE_Others"


class IncomeCategoryPriority(models.IntegerChoices):
    """
    Choices for IncomeCategory priority value.
    """

    REGULAR = 201, "INCOME_Regular"
    IRREGULAR = 202, "INCOME_Irregular"
