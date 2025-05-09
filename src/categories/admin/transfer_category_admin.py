from django.contrib import admin

from categories.models.transfer_category_model import TransferCategory


@admin.register(TransferCategory)
class TransferCategoryAdmin(admin.ModelAdmin):
    """Custom admin view for TransferCategory model."""

    list_display = ("name", "category_type", "priority", "budget", "owner", "is_active")
    list_filter = ("budget", "category_type", "priority", "is_active")
