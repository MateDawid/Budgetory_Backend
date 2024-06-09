from django.db import models


class Entity(models.Model):
    """Entity model for seller (or source of income) representation."""

    budget = models.ForeignKey(
        'budgets.Budget', on_delete=models.CASCADE, related_name='entities', null=False, blank=False
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    deposit = models.OneToOneField(
        'deposits.Deposit', on_delete=models.SET_NULL, related_name='entity', null=True, blank=True
    )

    class Meta:
        verbose_name_plural = 'entities'
        unique_together = (
            'name',
            'budget',
        )

    def __str__(self):
        return f'{self.name} ({self.budget.name})'
