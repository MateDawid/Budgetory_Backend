from django.contrib import admin

from categories.models.income_category_model import IncomeCategory


@admin.register(IncomeCategory)
class IncomeCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for IncomeCategory model."""

    list_display = ("name", "priority", "budget", "owner", "is_active")
    list_filter = ("budget", "priority", "is_active")
