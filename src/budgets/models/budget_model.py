from django.conf import settings
from django.db import models


class Budget(models.Model):
    """Model for object gathering all data like incomes, expenses and predictions for particular Budget."""

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True, max_length=300)
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name="budgets", blank=True)
    currency = models.CharField(max_length=3)

    def __str__(self) -> str:
        """
        Method for returning string representation of Budget model instance.

        Returns:
            str: String representation of Budget model instance.
        """
        return self.name
