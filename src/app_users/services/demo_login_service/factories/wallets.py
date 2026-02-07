from enum import StrEnum

from app_users.models import User
from wallets.models import Wallet


class WalletName(StrEnum):
    DAILY = "Daily"
    LONG_TERM = "Long term"


def create_wallets(user: User) -> list[Wallet]:
    """
    Service to create Wallets for demo User.

    Returns:
        list[Wallet]: List of created Wallet instances.
    """
    return Wallet.objects.bulk_create(
        [
            Wallet(name=WalletName.DAILY, description="Wallet for daily expenses.", currency_id="EUR", owner=user),
            Wallet(
                name=WalletName.LONG_TERM,
                description="Wallet for long term investments and savings.",
                currency_id="EUR",
                owner=user,
            ),
        ]
    )
