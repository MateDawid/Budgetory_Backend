from categories.models import ExpenseCategory, IncomeCategory
from django.contrib import admin


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for IncomeCategory model."""

    list_display = ('name', 'group', 'budget', 'owner', 'is_active')
    list_filter = ('budget', 'budget__owner__email', 'group')


@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for ExpenseCategory model."""

    list_display = ('name', 'group', 'budget', 'owner', 'is_active')
    list_filter = ('budget', 'budget__owner__email', 'group')
