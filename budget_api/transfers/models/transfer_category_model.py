from django.conf import settings
from django.db import models


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    group = models.ForeignKey(
        'transfers.TransferCategoryGroup', blank=False, null=False, on_delete=models.CASCADE, related_name='categories'
    )
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

    class Meta:
        verbose_name_plural = 'transfer categories'

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f'{self.name} ({self.group.name})'
