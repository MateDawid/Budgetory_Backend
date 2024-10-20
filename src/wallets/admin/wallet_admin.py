from django.contrib import admin

from wallets.models import Wallet
from wallets.models.wallet_deposit_model import WalletDeposit


class WalletDepositInline(admin.TabularInline):
    """Inline for Deposit model assigned to Wallet."""

    model = WalletDeposit
    fields = ("deposit", "planned_weight")
    readonly_fields = ("deposit", "planned_weight")
    can_delete = False
    show_change_link = True

    def has_change_permission(self, request, obj=None) -> bool:
        """
        Overridden to prevent changing TutorialToken in inline.

        Returns:
            bool: False
        """
        return False

    def has_add_permission(self, request, obj):
        """
        Overridden to prevent adding TutorialToken in inline.

        Returns:
            bool: False
        """
        return False


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Custom admin view for Transfer model."""

    list_display = ("name", "budget")
    fields = ("name", "budget")
    list_filter = ("budget",)
    inlines = (WalletDepositInline,)
