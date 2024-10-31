from django.contrib import admin

from transfers.models.transfer_model import Transfer


@admin.register(Transfer)
class TransferAdmin(admin.ModelAdmin):
    """Custom admin view for Transfer model."""

    list_display = ("date", "period", "entity", "name", "category", "value", "deposit")
    list_filter = ("date", "period__budget", "period", "entity", "category", "deposit")
