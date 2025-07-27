from django.contrib import admin

from entities.models.deposit_model import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ("name", "budget", "description", "is_active", "owner")
    list_filter = ("budget__name", "is_active", "owner")
