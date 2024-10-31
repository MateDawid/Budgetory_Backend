from django.contrib import admin

from categories.models.expense_category_model import ExpenseCategory


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for ExpenseCategory model."""

    list_display = ("name", "priority", "budget", "owner", "is_active")
    list_filter = ("budget", "budget__owner__email", "priority", "is_active")
