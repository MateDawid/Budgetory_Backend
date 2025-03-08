from django.contrib import admin

from budgets.models.budget_model import Budget


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    """Custom admin view for Budget model."""

    list_display = ("name",)
