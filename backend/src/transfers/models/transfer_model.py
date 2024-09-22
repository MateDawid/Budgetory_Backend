from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from transfers.managers.expense_manager import ExpenseManager
from transfers.managers.income_manager import IncomeManager


class Transfer(models.Model):
    """Transfer model for representing cash flow between Entities"""

    name = models.CharField(max_length=255, blank=False, null=False)
    description = models.CharField(max_length=255, blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(null=False, blank=False)
    period = models.ForeignKey("budgets.BudgetingPeriod", on_delete=models.PROTECT, related_name="transfers")
    entity = models.ForeignKey("entities.Entity", on_delete=models.PROTECT, related_name="entity_transfers")
    deposit = models.ForeignKey("entities.Deposit", on_delete=models.PROTECT, related_name="deposit_transfers")
    category = models.ForeignKey("categories.TransferCategory", on_delete=models.PROTECT, related_name="transfers")

    objects = models.Manager()
    incomes = IncomeManager()
    expenses = ExpenseManager()

    class Meta:
        verbose_name_plural = "transfers"
        constraints = (
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_value_gt_0",
                check=models.Q(value__gt=Decimal("0.00")),
            ),
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_deposit_and_entity_not_the_same",
                check=models.Q(_negated=True, entity=models.F("deposit")),
            ),
        )

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

    def __str__(self) -> str:
        """
        Returns string representation of Transfer model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f"{self.date} | {self.category} | {self.value}"
