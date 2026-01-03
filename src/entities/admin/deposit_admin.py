from django.contrib import admin

from entities.models.deposit_model import Deposit


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ("name", "wallet", "description", "is_active")
    list_filter = ("wallet__name", "is_active")
