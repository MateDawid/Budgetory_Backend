from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class BudgetingPeriod(models.Model):
    """Model for period in which budget will be calculated and reported."""

    name = models.CharField(max_length=128)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgeting_periods')
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            'name',
            'user',
        )

    def __str__(self):
        """String representation of BudgetingPeriod model instance."""
        return f'{self.name} ({self.user.email})'

    def save(self, *args, **kwargs):
        """Override save method to execute clean() method before saving model in database."""
        self.clean()
        super().save(*args, **kwargs)

    def clean_is_active(self):
        """Check if is_active field is valid. If is_active not given, pass it to default model validation."""
        if self.is_active is None:
            return
        if self.is_active and self.user.budgeting_periods.filter(is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError('is_active: User already has active budgeting period.', code='active-invalid')

    def clean_dates(self):
        """Check if date_start and date_end fields are valid. If date_start or date_end not given,
        pass them to default model validation."""
        if self.date_start is None or self.date_end is None:
            return
        if self.date_start >= self.date_end:
            raise ValidationError('start_date: Start date should be earlier than end date.', code='date-invalid')
        if (
            self.user.budgeting_periods.filter(
                Q(date_start__lte=self.date_start, date_end__gte=self.date_start)
                | Q(date_start__lte=self.date_end, date_end__gte=self.date_end)
                | Q(date_start__gte=self.date_start, date_end__lte=self.date_end)
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                "date_start: Budgeting period date range collides with other user's budgeting periods.",
                code='period-range-invalid',
            )

    def clean(self):
        """Clean BudgetingPeriod input data before saving in database."""
        self.clean_is_active()
        self.clean_dates()
