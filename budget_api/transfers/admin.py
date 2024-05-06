from django.contrib import admin
from transfers.models import TransferCategory


@admin.register(TransferCategory)
class TransferCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for TransferCategory model."""

    list_display = ('name', 'group', 'owner', 'is_active')
    list_filter = ('group__budget', 'group__budget__owner__email')
