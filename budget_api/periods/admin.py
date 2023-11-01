from django.contrib import admin
from periods.models import BudgetingPeriod


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ('name', 'user', 'date_start', 'date_end', 'is_active')
    list_filter = ('is_active', 'user__email')
