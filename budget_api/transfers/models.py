from django.conf import settings
from django.db import models


class GlobalTransferCategoryManager(models.Manager):
    """Manager for global TransferCategories."""

    def get_queryset(self):
        return super().get_queryset().filter(scope=TransferCategory.GLOBAL)


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    GLOBAL = 'GLOBAL'
    PERSONAL = 'PERSONAL'
    SCOPE_CHOICES = (
        (GLOBAL, 'Global'),
        (PERSONAL, 'Personal'),
    )
    INCOME = 'INCOME'
    EXPENSE = 'EXPENSE'
    CATEGORY_TYPE_CHOICES = (
        (INCOME, 'Income'),
        (EXPENSE, 'Expense'),
    )

    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    category_type = models.CharField(max_length=7, choices=CATEGORY_TYPE_CHOICES)
    scope = models.CharField(max_length=8, choices=SCOPE_CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name='personal_transfer_categories',
    )
    is_active = models.BooleanField(default=True)
    objects = models.Manager()
    global_transfer_categories = GlobalTransferCategoryManager()

    class Meta:
        verbose_name_plural = 'transfer categories'

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return self.name
