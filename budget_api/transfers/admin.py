from django.contrib import admin
from transfers.models.transfer_category_group_model import TransferCategoryGroup
from transfers.models.transfer_category_model import TransferCategory

admin.site.register(TransferCategory)


@admin.register(TransferCategoryGroup)
class TransferCategoryGroupAdmin(admin.ModelAdmin):
    """Custom admin view for TransferCategoryGroup model."""

    list_display = ('name', 'transfer_type', 'budget')
    list_filter = ('transfer_type', 'budget__owner__email')
