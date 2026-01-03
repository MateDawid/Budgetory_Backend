from django.contrib import admin

from entities.models.entity_model import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ("name", "wallet", "description", "is_active", "is_deposit")
    list_filter = ("wallet__name", "is_active")
