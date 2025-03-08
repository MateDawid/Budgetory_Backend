from __future__ import annotations

from django.db import models


class CategoryPriority(models.IntegerChoices):
    REGULAR = 1, "📈 01. Regular"
    IRREGULAR = 2, "📈 02. Irregular"
    MOST_IMPORTANT = 3, "📉 01. Most important"
    DEBTS = 4, "📉 02. Debts"
    SAVINGS = 5, "📉 03. Savings"
    OTHERS = 6, "📉 04. Others"

    @classmethod
    def income_priorities(cls) -> tuple[CategoryPriority, ...]:
        """
        Property to return only Income categories priorities.

        Returns:
            tuple[CategoryPriority, ...]: Tuple containing selected CategoryPriority choices.
        """
        return cls.REGULAR, cls.IRREGULAR

    @classmethod
    def expense_priorities(cls) -> tuple[CategoryPriority, ...]:
        """
        Property to return only Expense categories priorities.

        Returns:
            tuple[CategoryPriority, ...]: Tuple containing selected CategoryPriority choices.
        """
        return cls.MOST_IMPORTANT, cls.DEBTS, cls.SAVINGS, cls.OTHERS
