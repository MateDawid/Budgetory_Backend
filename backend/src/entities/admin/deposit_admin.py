from django.contrib import admin
from entities.models.deposit_model import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ("name", "budget", "description", "is_active")
    list_filter = ("budget__name", "budget__owner__email", "is_active")
