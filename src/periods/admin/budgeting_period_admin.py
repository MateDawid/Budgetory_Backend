from django.contrib import admin

from periods.models import BudgetingPeriod


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ("name", "budget", "status", "date_start", "date_end")
    list_filter = ("budget__name", "status")
