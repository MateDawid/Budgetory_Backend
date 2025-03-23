from django.contrib import admin

from predictions.models.expense_prediction_model import ExpensePrediction


@admin.register(ExpensePrediction)
class ExpensePredictionAdmin(admin.ModelAdmin):
    """Custom admin view for ExpensePrediction model."""

    list_display = ("period", "category", "initial_value", "current_value")
    list_filter = ("period__budget__name",)
    readonly_fields = ("initial_value",)
