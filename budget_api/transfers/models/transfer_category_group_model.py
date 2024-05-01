from django.db import models


class TransferCategoryGroup(models.Model):
    """TransferCategoryGroup model for grouping TransferCategory model instances."""

    class TransferTypes(models.IntegerChoices):
        """Choices for deposit_type value."""

        INCOME = 0, 'Income'
        EXPENSE = 1, 'Expense'
        RELOCATION = 2, 'Relocation'

    budget = models.ForeignKey(
        'budgets.Budget', on_delete=models.CASCADE, related_name='category_groups', null=False, blank=False
    )
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True, null=True)
    transfer_type = models.PositiveSmallIntegerField(choices=TransferTypes.choices, null=False, blank=False)

    class Meta:
        verbose_name_plural = 'transfer category groups'
        unique_together = (
            'name',
            'budget',
        )

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategoryGroup model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'{self.name} ({self.budget.name})'
