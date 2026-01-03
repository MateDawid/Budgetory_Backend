from django.db import models

from periods.models.choices.period_status import PeriodStatus


class Period(models.Model):
    """Model for period in which Wallet data will be calculated and reported."""

    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.CASCADE, related_name="periods")
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
        help_text="Reference to the previous period within the same wallet",
    )

    class Meta:
        unique_together = (
            "name",
            "wallet",
        )

    def __str__(self) -> str:
        """
        Method for returning string representation of Period model instance.

        Returns:
            str: String representation of Period model instance.
        """
        return f"{self.name} ({self.wallet.name})"

    def save(self, *args, **kwargs):
        """
        Override save method to calculate and set previous_period.
        """
        if not self.previous_period and self.wallet_id:
            last_period = (
                Period.objects.filter(wallet=self.wallet, date_end__lt=self.date_start)
                .exclude(pk=self.pk)
                .order_by("-date_end")
                .first()
            )

            if last_period:
                self.previous_period = last_period

        super().save(*args, **kwargs)
