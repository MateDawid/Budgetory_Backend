from django.contrib import admin

from transfers.models.transfer_model import Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Custom admin view for Transfer model."""

    list_display = ("transfer_type", "date", "period", "name", "deposit", "entity", "category", "value", "description")
    list_filter = ("date", "period__wallet", "period", "transfer_type", "entity", "category", "deposit")
