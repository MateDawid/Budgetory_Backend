from django.contrib import admin

from transfers.admin.transfer_admin import TransferAdmin
from transfers.models.income_model import Income


@admin.register(Income)
class IncomeAdmin(TransferAdmin):
    """Custom admin view for Income model."""
