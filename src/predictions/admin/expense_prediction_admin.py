from django.contrib import admin

from predictions.models.expense_prediction_model import ExpensePrediction


@admin.register(ExpensePrediction)
class ExpensePredictionAdmin(admin.ModelAdmin):
    """Custom admin view for ExpensePrediction model."""

    list_display = ("period", "deposit", "category", "initial_plan", "current_plan")
    list_filter = ("period__budget__name", "period", "deposit", "category")
