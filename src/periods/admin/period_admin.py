from django.contrib import admin

from periods.models import Period


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    """Custom admin view for Period model."""

    list_display = ("name", "wallet", "status", "date_start", "date_end")
    list_filter = ("wallet__name", "status")
