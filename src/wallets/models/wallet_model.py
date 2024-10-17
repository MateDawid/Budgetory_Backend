from django.db import models


class Wallet(models.Model):
    """Expense proxy model for Transfer with ExpenseCategory as category."""

    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE, related_name="wallets")
    name = models.CharField(max_length=255, blank=False, null=False)

    class Meta:
        verbose_name_plural = "wallets"
        unique_together = (
            "name",
            "budget",
        )

    def __str__(self):
        return self.name
