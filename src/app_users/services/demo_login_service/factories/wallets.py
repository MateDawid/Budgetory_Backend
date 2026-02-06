from enum import StrEnum

from wallets.models import Currency, Wallet


class WalletName(StrEnum):
    DAILY = "Daily"
    LONG_TERM = "Long term"


def create_wallets() -> list[Wallet]:
    """
    Service to create Wallets for demo User.

    Returns:
        list[Wallet]: List of created Wallet instances.
    """
    currency = Currency.objects.get(name="EUR")
    return Wallet.objects.bulk_create(
        [
            Wallet(name=WalletName.DAILY, description="Wallet for daily expenses.", currency=currency),
            Wallet(
                name=WalletName.LONG_TERM,
                description="Wallet for long term investments and savings.",
                currency=currency,
            ),
        ]
    )
