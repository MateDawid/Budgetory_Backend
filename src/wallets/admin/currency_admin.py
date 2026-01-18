from django.contrib import admin

from wallets.models.currency_model import Currency


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    """Custom admin view for Currency model."""

    list_display = ("name",)
