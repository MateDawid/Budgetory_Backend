from django.db import models

from budgets.models.choices.period_status import PeriodStatus


class BudgetingPeriod(models.Model):
    """Model for period in which Budget data will be calculated and reported."""

    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE, related_name="periods")
    status = models.PositiveSmallIntegerField(choices=PeriodStatus.choices, null=False, blank=False)
    name = models.CharField(max_length=128)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)

    class Meta:
        unique_together = (
            "name",
            "budget",
        )

    def __str__(self) -> str:
        """
        Method for returning string representation of BudgetingPeriod model instance.

        Returns:
            str: String representation of BudgetingPeriod model instance.
        """
        return f"{self.name} ({self.budget.name})"
