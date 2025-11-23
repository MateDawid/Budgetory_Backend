from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import CheckConstraint, Q


class ExpensePrediction(models.Model):
    """ExpensePrediction model for planned expenses in particular BudgetingPeriod."""

    period = models.ForeignKey("budgets.BudgetingPeriod", on_delete=models.CASCADE, related_name="expense_predictions")
    deposit = models.ForeignKey("entities.Deposit", on_delete=models.CASCADE, related_name="expense_predictions")
    category = models.ForeignKey(
        "categories.TransferCategory",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="expense_predictions",
    )
    initial_plan = models.DecimalField(max_digits=10, decimal_places=2, default=None, blank=True, null=True)
    current_plan = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("period", "category")
        constraints = (
            CheckConstraint(
                check=Q(initial_plan__gte=Decimal("0.00")),
                name="initial_plan_gte_0",
            ),
            CheckConstraint(
                check=Q(current_plan__gte=Decimal("0.00")),
                name="current_plan_gte_0",
            ),
        )

    def __str__(self) -> str:
        """
        Returns string representation of ExpensePrediction model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f"[{self.period.name}] {getattr(self.category, 'name', '❗Not categorized')}"

    def save(self, *args, **kwargs) -> None:
        """
        Override save method to execute validation before saving model in database.
        """
        self._validate_category()
        super().save(*args, **kwargs)

    def _validate_category(self) -> None:
        """
        Checks if category Budget and period Budget are the same.

        Raises:
            ValidationError: Raised when category Budget and period Budget are not the same.
        """
        if self.category is None:
            return
        if self.category.budget != self.period.budget:
            raise ValidationError("Budget for period and category fields is not the same.", code="budget-invalid")
        if self.category.deposit != self.deposit:
            raise ValidationError("Category Deposit different than Prediction Deposit", code="deposit-invalid")
