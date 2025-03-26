from django.contrib import admin

from budgets.models.budgeting_period_model import BudgetingPeriod


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ("name", "budget", "status", "date_start", "date_end")
    list_filter = ("budget__name", "status")
