from django.conf import settings
from django.db import models


class IncomeCategory(models.Model):
    """IncomeCategory model for categorizing income Transfers."""

    class Meta:
        verbose_name_plural = 'income categories'

    class Groups(models.IntegerChoices):
        """Choices for group value."""

        REGULAR = 1, 'Regular'
        IRREGULAR = 2, 'Irregular'

    budget = models.ForeignKey('budgets.Budget', on_delete=models.CASCADE, related_name='income_categories')
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='income_categories',
    )
    is_active = models.BooleanField(default=True)
    group = models.PositiveSmallIntegerField(choices=Groups.choices, null=True, blank=True)

    def __str__(self) -> str:
        """
        Returns string representation of IncomeCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'{self.__class__} {self.name} ({self.budget.name})'


class ExpenseCategory(models.Model):
    """ExpenseCategory model for categorizing expense Transfers."""

    class Meta:
        verbose_name_plural = 'expense categories'

    class Groups(models.IntegerChoices):
        """Choices for group value."""

        MOST_IMPORTANT = 1, 'Most important'
        DEBTS = 2, 'Debts'
        SAVINGS = 3, 'Savings'
        OTHERS = 4, 'Others'

    budget = models.ForeignKey('budgets.Budget', on_delete=models.CASCADE, related_name='expense_categories')
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='expense_categories',
    )
    is_active = models.BooleanField(default=True)
    group = models.PositiveSmallIntegerField(choices=Groups.choices, null=True, blank=True)

    def __str__(self) -> str:
        """
        Returns string representation of ExpenseCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'{self.__class__} {self.name} ({self.budget.name})'
