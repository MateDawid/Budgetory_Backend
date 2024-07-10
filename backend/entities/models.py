from django.db import models


class Entity(models.Model):
    """Entity model for Transfer actor (payer or receiver) representation."""

    budget = models.ForeignKey(
        'budgets.Budget', on_delete=models.CASCADE, related_name='entities', null=False, blank=False
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_deposit = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'entities'
        unique_together = (
            'name',
            'budget',
        )

    def __str__(self):
        return f'{self.name} ({self.budget.name})'


class Deposit(Entity):
    """Deposit proxy model for Entity owned by Budget member representation."""

    class DepositManager(models.Manager):
        """Manager for Deposit Entities."""

        def get_queryset(self):
            return super().get_queryset().filter(is_deposit=True)

    class Meta:
        proxy = True
        verbose_name_plural = 'deposits'

    objects = DepositManager()
