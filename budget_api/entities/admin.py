from django.contrib import admin
from entities.models import Entity


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    """Custom admin view for Deposit model."""

    list_display = ('name', 'description', 'is_personal', 'user')
    list_filter = ('is_personal', 'user__email')
