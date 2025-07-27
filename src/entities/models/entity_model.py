from django.conf import settings
from django.db import models

from entities.managers.deposit_manager import DepositManager


class Entity(models.Model):
    """Entity model for Transfer actor (payer or receiver) representation."""

    budget = models.ForeignKey(
        "budgets.Budget", on_delete=models.CASCADE, related_name="entities", null=False, blank=False
    )
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    is_deposit = models.BooleanField(default=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="deposits",  # Entity.owner field dedicated to be used only in terms of Deposit ownership.
    )

    objects = models.Manager()
    deposits = DepositManager()

    class Meta:
        verbose_name_plural = "entities"
        unique_together = (
            "name",
            "budget",
        )
        constraints = (
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_owner_value_only_on_deposit",
                check=models.Q(is_deposit=True) | models.Q(is_deposit=False, owner__isnull=True),
            ),
        )

    def __str__(self) -> str:
        """
        Method for returning string representation of Entity model instance.

        Returns:
            str: String representation of Entity model instance.
        """
        return f"{self.name} ({self.budget.name})"
