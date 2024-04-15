from django.conf import settings
from django.db import models


class Deposit(models.Model):
    """Deposit model where revenues are collected and from which payments are made."""

    class DepositTypes(models.IntegerChoices):
        """Choices for deposit_type value."""

        PERSONAL = 0, 'Personal'
        COMMON = 1, 'Common'
        RESERVES = 2, 'Reserves'
        INVESTMENTS = 3, 'Investments'
        SAVINGS = 4, 'Savings'

    budget = models.ForeignKey(
        'budgets.Budget', on_delete=models.CASCADE, related_name='deposits', null=False, blank=False
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    deposit_type = models.PositiveSmallIntegerField(choices=DepositTypes.choices, null=False, blank=False)
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, related_name='owned_deposits', null=True, blank=True
    )

    class Meta:
        unique_together = (
            'name',
            'budget',
        )

    def __str__(self) -> str:
        """
        Returns string representation of Deposit model instance.

        Returns:
        str: Custom string representation of instance.
        """
        return f'{self.name} ({self.budget.name})'
