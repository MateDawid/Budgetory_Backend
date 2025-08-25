from django.db import models

from budgets.models.choices.period_status import PeriodStatus


class BudgetingPeriod(models.Model):
    """Model for period in which Budget data will be calculated and reported."""

    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE, related_name="periods")
    status = models.PositiveSmallIntegerField(choices=PeriodStatus.choices, null=False, blank=False)
    name = models.CharField(max_length=128)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    previous_period = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="next_periods",
        help_text="Reference to the previous budgeting period within the same budget",
    )

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

    def save(self, *args, **kwargs):
        """
        Override save method to calculate and set previous_period.
        """
        if not self.previous_period and self.budget_id:
            last_period = (
                BudgetingPeriod.objects.filter(budget=self.budget, date_end__lt=self.date_start)
                .exclude(pk=self.pk)
                .order_by("-date_end")
                .first()
            )

            if last_period:
                self.previous_period = last_period

        super().save(*args, **kwargs)
