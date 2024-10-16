from django.contrib import admin

from transfers.admin.transfer_admin import TransferAdmin
from transfers.models.expense_model import Expense


@admin.register(Expense)
class ExpenseAdmin(TransferAdmin):
    """Custom admin view for Expense model."""
