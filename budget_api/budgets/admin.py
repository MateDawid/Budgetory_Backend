from budgets.models import BudgetingPeriod
from django.contrib import admin


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ('name', 'user', 'date_start', 'date_end', 'is_active')
    list_filter = ('is_active', 'user__email')
