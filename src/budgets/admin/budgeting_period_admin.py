from django.contrib import admin

from budgets.models.budgeting_period_model import BudgetingPeriod


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ("name", "budget", "date_start", "date_end", "is_active")
    list_filter = ("is_active", "budget__name", "budget__owner__email")
