from django.contrib import admin
from entities.models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ('name', 'description', 'type', 'user')
    list_filter = ('type', 'user__email')
