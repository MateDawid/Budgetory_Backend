from budgets.models import Budget, BudgetingPeriod
from django.contrib import admin


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Custom admin view for Budget model."""

    list_display = ('name', 'owner')
    list_filter = ('owner__email',)


@admin.register(BudgetingPeriod)
class BudgetingPeriodAdmin(admin.ModelAdmin):
    """Custom admin view for BudgetingPeriod model."""

    list_display = ('name', 'user', 'date_start', 'date_end', 'is_active')
    list_filter = ('is_active', 'user__email')
