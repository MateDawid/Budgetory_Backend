from django.contrib import admin

from entities.models import Deposit
from wallets.models import Wallet


class DepositInline(admin.TabularInline):
    """Inline for Deposit model assigned to Wallet."""

    model = Deposit
    fields = ("name",)
    readonly_fields = ("name",)
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
    inlines = (DepositInline,)
