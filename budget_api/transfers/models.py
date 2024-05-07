from django.conf import settings
from django.db import models


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    class ExpenseGroups(models.IntegerChoices):
        """Choices for deposit_type value."""

        MOST_IMPORTANT = 0, 'Most important'
        DEBTS = 1, 'Debts'
        SAVINGS = 2, 'Savings'
        OTHERS = 3, 'Others'

    class IncomeGroups(models.IntegerChoices):
        """Choices for deposit_type value."""

        REGULAR = 0, 'Regular'
        IRREGULAR = 1, 'Irregular'

    budget = models.ForeignKey('budgets.Budget', on_delete=models.CASCADE, related_name='transfer_categories')
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='personal_categories',
    )
    is_active = models.BooleanField(default=True)
    expense_group = models.PositiveSmallIntegerField(choices=ExpenseGroups.choices, null=True, blank=True)
    income_group = models.PositiveSmallIntegerField(choices=IncomeGroups.choices, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'transfer categories'

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'{self.name} ({self.budget.name})'
