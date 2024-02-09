from deposits.models import Deposit
from django.contrib import admin


@admin.register(Deposit)
class DepositAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ('name', 'user', 'description', 'is_active')
    list_filter = ('is_active', 'user__email')
