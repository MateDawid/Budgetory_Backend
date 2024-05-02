from django.db import models


class GlobalEntityManager(models.Manager):
    """Manager for global Entities."""

    def get_queryset(self):
        return super().get_queryset().filter(type=Entity.GLOBAL)


class Entity(models.Model):
    """Entity model for seller (or source of income) representation."""

    budget = models.ForeignKey(
        'budgets.Budget', on_delete=models.CASCADE, related_name='entities', null=False, blank=False
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        verbose_name_plural = 'entities'
        unique_together = (
            'name',
            'budget',
        )
