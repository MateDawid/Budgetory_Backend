from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models

from categories.models.choices.category_type import CategoryType
from transfers.managers.expense_manager import ExpenseManager
from transfers.managers.income_manager import IncomeManager


class Transfer(models.Model):
    """Transfer model for representing cash flow between Entities"""

    transfer_type = models.PositiveSmallIntegerField(choices=CategoryType.choices, null=False, blank=False)
    name = models.CharField(max_length=255, blank=True, null=False)
    description = models.TextField(blank=True, null=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(null=False, blank=False)
    period = models.ForeignKey(
        "periods.BudgetingPeriod", blank=False, null=False, on_delete=models.CASCADE, related_name="transfers"
    )
    entity = models.ForeignKey(
        "entities.Entity", on_delete=models.SET_NULL, blank=True, null=True, related_name="entity_transfers"
    )
    deposit = models.ForeignKey(
        "entities.Deposit", on_delete=models.CASCADE, blank=False, null=False, related_name="deposit_transfers"
    )
    category = models.ForeignKey(
        "categories.TransferCategory", on_delete=models.SET_NULL, blank=True, null=True, related_name="transfers"
    )

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
        self.validate_period()
        self.validate_deposit()
        super().save(*args, **kwargs)

    def validate_budget(self) -> None:
        """
        Checks if budget fields for period, category, entity and deposit are the same.

        Raises:
            ValidationError: Raised when different budget for one of period, category, entity and deposit fields.
        """
        field_budgets = [self.deposit.budget]
        if self.category:
            field_budgets.append(self.category.budget)
        if self.entity:
            field_budgets.append(self.entity.budget)
        if not all((self.period.budget == field_budget for field_budget in field_budgets)):
            raise ValidationError(
                "Budget for period, category, entity and deposit fields is not the same.", code="budget-invalid"
            )

    def validate_period(self) -> None:
        """
        Checks if Transfer "date" field value is between given "period" date range.

        Raises:
            ValidationError: Raised when "date" field is out of given "period" date range.
        """
        if not (self.period.date_start <= self.date <= self.period.date_end):
            raise ValidationError("Transfer date not in period date range.", code="date-invalid")

    def validate_deposit(self) -> None:
        """
        Checks if Entity instance from "deposit" field is marked as Deposit proxy.

        Raises:
            ValidationError: Raised when is_deposit value is False for "deposit" field object.
        """
        if not self.deposit.is_deposit:
            raise ValidationError('Value of "deposit" field has to be Deposit model instance.', code="deposit-invalid")

    def __str__(self) -> str:
        """
        Returns string representation of Transfer model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f"{self.date} | {self.category} | {self.value}"
