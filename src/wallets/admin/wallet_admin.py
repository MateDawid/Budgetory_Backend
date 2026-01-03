from django.contrib import admin

from wallets.models.wallet_model import Wallet


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Custom admin view for Wallet model."""

    list_display = ("name",)
