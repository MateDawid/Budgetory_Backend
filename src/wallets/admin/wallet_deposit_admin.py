from django.contrib import admin

from wallets.models.wallet_deposit_model import WalletDeposit


@admin.register(WalletDeposit)
class WalletDepositAdmin(admin.ModelAdmin):
    """Custom admin view for WalletDeposit model."""

    list_display = ("wallet", "deposit", "planned_weight")
    fields = ("wallet", "deposit", "planned_weight")
    list_filter = ("wallet",)
