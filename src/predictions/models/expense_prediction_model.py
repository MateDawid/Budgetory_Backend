from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q


class ExpensePrediction(models.Model):
    """ExpensePrediction model for planned expenses in particular BudgetingPeriod."""

    period = models.ForeignKey("budgets.BudgetingPeriod", on_delete=models.CASCADE, related_name="expense_predictions")
    category = models.ForeignKey(
        "categories.TransferCategory", on_delete=models.CASCADE, related_name="expense_predictions"
    )
    initial_value = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    current_value = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ("period", "category")
        constraints = (
            CheckConstraint(
                check=Q(initial_value__gt=Decimal("0.00")),
                name="initial_value_gte_0",
            ),
            CheckConstraint(
                check=Q(current_value__gt=Decimal("0.00")),
                name="current_value_gte_0",
            ),
        )

    def __str__(self) -> str:
        """
        Returns string representation of ExpensePrediction model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f"[{self.period.name}] {self.category.name}"

    def save(self, *args, **kwargs) -> None:
        """
        Override save method to execute validation before saving model in database.
        """
        self.validate_budget()
        super().save(*args, **kwargs)

    def validate_budget(self) -> None:
        """
        Checks if category Budget and period Budget are the same.

        Raises:
            ValidationError: Raised when category Budget and period Budget are not the same.
        """
        if self.period.budget != self.category.budget:
            raise ValidationError("Budget for period and category fields is not the same.", code="budget-invalid")
