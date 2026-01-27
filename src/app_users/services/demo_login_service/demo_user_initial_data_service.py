from app_users.models import User
from entities.models import Entity
from wallets.models import Currency, Wallet


def create_initial_data_for_demo_user(user: User):
    """
    Creates initial data for demo user.

    Args:
        user (User): User instance.
    """
    daily_wallet, long_term_wallet = create_two_demo_wallets(user)
    create_demo_entities(daily_wallet, long_term_wallet)


def create_two_demo_wallets(user: User) -> tuple[Wallet, Wallet]:
    """
    Creates Wallets for demo User.

    Args:
        user (User): User instance.

    Returns:
        tuple[Wallet, Wallet]: Two Wallets for demo User.
    """
    currency = Currency.objects.get(name="EUR")
    daily_wallet = Wallet.objects.create(name="Daily", currency=currency, description="Wallet for daily expenses.")
    daily_wallet.members.add(user)
    long_term_wallet = Wallet.objects.create(
        name="Long term", currency=currency, description="Wallet for long term investments and savings."
    )
    long_term_wallet.members.add(user)
    return daily_wallet, long_term_wallet


def create_demo_entities(daily_wallet: Wallet, long_term_wallet: Wallet):
    """
    Creates data for demo Daily expenses wallet.

    Args:
        daily_wallet (Wallet): "Daily" Wallet instance.
        long_term_wallet (Wallet): "Long term" Wallet instance.
    """
    return Entity.objects.bulk_create(
        [
            # Deposits for "Daily Wallet"
            Entity(
                wallet=daily_wallet,
                name="Personal account",
                description="Account for personal User expenses and incomes.",
                is_deposit=True,
            ),
            Entity(
                wallet=daily_wallet,
                name="Common account",
                description="Account for common expenses and incomes.",
                is_deposit=True,
            ),
            # Deposits for "Long term" Wallet
            Entity(
                wallet=long_term_wallet,
                name="Treasury bonds",
                description="Funds allocated in treasury bonds.",
                is_deposit=True,
            ),
            Entity(
                wallet=long_term_wallet,
                name="ETF",
                description="Funds allocated in ETF.",
                is_deposit=True,
            ),
            Entity(
                wallet=long_term_wallet,
                name="Gold",
                description="Funds allocated in gold.",
                is_deposit=True,
            ),
            # Entities for "Daily" Wallet
            Entity(wallet=daily_wallet, name="Employer", description="Employer hiring User."),
            Entity(wallet=daily_wallet, name="Buyer", description="Buyer of stuff that User's selling."),
            Entity(wallet=daily_wallet, name="Food seller", description="Seller that sells food."),
            Entity(wallet=daily_wallet, name="Bills taker", description="Entity that receives bills."),
            Entity(wallet=daily_wallet, name="Unexpected entity", description="Entity that charges unexpectedly."),
            # Entities for "Long term" Wallet
            Entity(
                wallet=long_term_wallet, name="Treasury bonds seller", description="Entity that sells treasury bonds."
            ),
            Entity(
                wallet=long_term_wallet,
                name="Treasury bonds value change",
                description="Entity for handling changes of treasury bonds value.",
            ),
            Entity(wallet=long_term_wallet, name="ETF seller", description="Entity that sells ETF."),
            Entity(
                wallet=long_term_wallet,
                name="ETF value change",
                description="Entity for handling changes of ETF value.",
            ),
            Entity(wallet=long_term_wallet, name="Gold seller", description="Entity that sells Gold."),
            Entity(
                wallet=long_term_wallet,
                name="Gold value change",
                description="Entity for handling changes of Gold value.",
            ),
        ]
    )
