from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Budget(models.Model):
    """Model for object gathering all data like incomes, expenses and predictions for particular budget."""

    name = models.CharField(max_length=128)
    description = models.TextField(null=True, blank=True, max_length=300)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_budgets')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='joined_budgets', blank=True)
    currency = models.CharField(max_length=3)

    class Meta:
        unique_together = (
            'name',
            'owner',
        )

    def __str__(self):
        """String representation of BudgetingPeriod model instance."""
        return f'{self.name} ({self.owner.email})'

    def save(self, *args, **kwargs):
        """Override save method to remove Budget owner from Budget members."""
        super().save(*args, **kwargs)
        self.members.remove(self.owner)


class BudgetingPeriod(models.Model):
    """Model for period in which Budget data will be calculated and reported."""

    budget = models.ForeignKey('budgets.Budget', on_delete=models.CASCADE, related_name='periods')
    name = models.CharField(max_length=128)
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    is_active = models.BooleanField(default=False)

    class Meta:
        unique_together = (
            'name',
            'budget',
        )

    def __str__(self):
        """String representation of BudgetingPeriod model instance."""
        return f'{self.name} ({self.budget.name})'

    def save(self, *args, **kwargs):
        """Override save method to execute clean() method before saving model in database."""
        self.clean()
        super().save(*args, **kwargs)

    def clean(self):
        """Clean BudgetingPeriod input data before saving in database."""
        self.clean_is_active()
        self.clean_dates()

    def clean_is_active(self):
        """Check if is_active field is valid. If is_active not given, pass it to default model validation."""
        if self.is_active and self.budget.periods.filter(is_active=True).exclude(pk=self.pk).exists():
            raise ValidationError('is_active: Active period already exists.', code='active-invalid')

    def clean_dates(self):
        """Check if date_start and date_end fields are valid. If date_start or date_end not given,
        pass them to default model validation."""
        if self.date_start >= self.date_end:
            raise ValidationError('start_date: Start date should be earlier than end date.', code='date-invalid')
        if (
            self.budget.periods.filter(
                Q(date_start__lte=self.date_start, date_end__gte=self.date_start)
                | Q(date_start__lte=self.date_end, date_end__gte=self.date_end)
                | Q(date_start__gte=self.date_start, date_end__lte=self.date_end)
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise ValidationError(
                'date_start: Period date range collides with other period in Budget.',
                code='period-range-invalid',
            )
