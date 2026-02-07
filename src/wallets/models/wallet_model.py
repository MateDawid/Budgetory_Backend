from django.conf import settings
from django.db import models


class Wallet(models.Model):
    """Model for object gathering all data like Periods, Deposits, Entities for particular Wallet."""

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True, max_length=300)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="wallets", on_delete=models.CASCADE, null=False, blank=False
    )
    currency = models.ForeignKey(
        "wallets.Currency", on_delete=models.SET_NULL, related_name="wallets", null=True, blank=False
    )

    def __str__(self) -> str:
        """
        Method for returning string representation of Wallet model instance.

        Returns:
            str: String representation of Wallet model instance.
        """
        return self.name
