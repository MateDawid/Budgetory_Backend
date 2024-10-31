from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class WalletDeposit(models.Model):
    """Model representing Deposit assignment to Wallet."""

    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.CASCADE, related_name="deposits")
    deposit = models.OneToOneField("entities.Deposit", on_delete=models.CASCADE, related_name="wallets")
    planned_weight = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name_plural = "wallet_deposits"
        unique_together = (
            "wallet",
            "deposit",
        )
        constraints = (
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_planned_weight_gte_0",
                check=models.Q(planned_weight__gte=Decimal("0.00")),
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_planned_weight_lte_100",
                check=models.Q(planned_weight__lte=Decimal("100.00")),
            ),
        )

    def __str__(self):
        """
        Returns string representation of model instance.

        Returns:
            str: String representation of model instance.
        """
        return f"{self.deposit.name} ({self.wallet.name})"

    def save(self, *args, **kwargs) -> None:
        """
        Method extended with additional validation of Budget values for Wallet and Deposit.
        """
        self.validate_budget()
        self.validate_weight_sum()
        super().save(*args, **kwargs)

    def validate_budget(self) -> None:
        """
        Checks if given Wallet and Deposit have the same Budget assigned.

        Raises:
            ValidationError: Raised when Budgets for Wallet and Deposit are not the same.
        """
        if self.deposit.budget.pk != self.wallet.budget.pk:
            raise ValidationError("Budget not the same for Wallet and Deposit.")

    def validate_weight_sum(self) -> None:
        """
        Checks if sum of planned_weight assigned to Wallet is less than 100.

        Raises:
            ValidationError: Raised when sum of planned_weight assigned to Wallet is greater than 100.
        """
        wallet_weights = self.wallet.deposits.exclude(pk=self.pk).values_list("planned_weight", flat=True)
        if sum([self.planned_weight, *wallet_weights]) > Decimal("100.00"):
            raise ValidationError("Sum of planned weights for single Wallet cannot be greater than 100.")
