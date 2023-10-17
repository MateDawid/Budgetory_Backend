from django.conf import settings
from django.db import models


class BudgetingPeriod(models.Model):
    """Model for period in which budget will be calculated and reported."""

    name = models.CharField(max_length=128)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='budgeting_periods')
    date_start = models.DateField(null=False, blank=False)
    date_end = models.DateField(null=False, blank=False)
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.name} ({self.user.email})'
