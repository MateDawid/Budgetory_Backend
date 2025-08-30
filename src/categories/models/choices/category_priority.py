from __future__ import annotations

from django.db import models


class CategoryPriority(models.IntegerChoices):
    REGULAR = 1, "📈 01. Regular"
    IRREGULAR = 2, "📈 02. Irregular"
    MOST_IMPORTANT = 3, "📉 01. Most important"
    DEBTS = 4, "📉 02. Debts"
    SAVINGS = 5, "📉 03. Savings"
    OTHERS = 6, "📉 04. Others"
    DEPOSIT_INCOME = 7, "📈 03. Deposit income"
    DEPOSIT_EXPENSE = 8, "📉 05. Deposit expense"

    @classmethod
    def income_priorities(cls) -> tuple[CategoryPriority, ...]:
        """
        Property to return only Income categories priorities.

        Returns:
            tuple[CategoryPriority, ...]: Tuple containing selected CategoryPriority choices.
        """
        return cls.REGULAR, cls.IRREGULAR, cls.DEPOSIT_INCOME

    @classmethod
    def expense_priorities(cls) -> tuple[CategoryPriority, ...]:
        """
        Property to return only Expense categories priorities.

        Returns:
            tuple[CategoryPriority, ...]: Tuple containing selected CategoryPriority choices.
        """
        return cls.MOST_IMPORTANT, cls.DEBTS, cls.SAVINGS, cls.OTHERS, cls.DEPOSIT_EXPENSE
