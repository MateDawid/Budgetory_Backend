from django.contrib import admin
from transfers.models import TransferCategory


@admin.register(TransferCategory)
class TransferCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for TransferCategory model."""

    list_display = ('name', 'expense_group', 'income_group', 'budget', 'owner', 'is_active')
    list_filter = ('budget', 'budget__owner__email', 'expense_group', 'income_group')
