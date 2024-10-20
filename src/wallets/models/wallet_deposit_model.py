from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class WalletDeposit(models.Model):
    """Model representing Deposit assignment to Wallet."""

    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.CASCADE, related_name="deposits")
    deposit = models.OneToOneField("entities.Deposit", on_delete=models.CASCADE, related_name="wallets")
    planned_weight = models.DecimalField(
        max_digits=3, decimal_places=0, default=Decimal(0), validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    class Meta:
        verbose_name_plural = "wallet_deposits"
        unique_together = (
            "wallet",
            "deposit",
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
        if sum([self.planned_weight, *self.wallet.deposits.values_list("planned_weight", flat=True)]) > Decimal("100"):
            raise ValidationError("Sum of planned weights for single Wallet has to be lower than 100.")
