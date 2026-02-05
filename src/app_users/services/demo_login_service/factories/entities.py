from enum import StrEnum

from entities.models import Deposit, Entity
from wallets.models import Wallet


class DepositName(StrEnum):
    # Deposits for "Daily" Wallet
    PERSONAL = "Personal account"
    COMMON = "Common account"
    # Deposits for "Long term" Wallet
    TREASURY_BONDS = "Treasury bonds"
    ETF = "ETF"
    GOLD = "Gold"


class EntityName(StrEnum):
    # Entities for "Daily" Wallet
    EMPLOYER = "Employer"
    BUYER = "Buyer"
    FOOD_SELLER = "Food seller"
    BILLS_TAKER = "Bills taker"
    UNEXPECTED_ENTITY = "Unexpected entity"
    DAILY_WALLET_TREASURY_BONDS_SELLER = "Seller of Treasury bonds"
    DAILY_WALLET_ETF_SELLER = "Seller of ETF"
    DAILY_WALLET_GOLD_SELLER = "Seller of Gold"
    # Entities for "Long term" Wallet
    LONG_TERM_WALLET_TREASURY_BONDS_SELLER = "Treasury bonds seller"
    TREASURY_BONDS_VALUE_CHANGE = "Treasury bonds value change"
    LONG_TERM_WALLET_ETF_SELLER = "ETF Seller"
    ETF_VALUE_CHANGE = "ETF value change"
    LONG_TERM_WALLET_GOLD_SELLER = "Gold seller"
    GOLD_VALUE_CHANGE = "Gold value change"


def create_deposits_and_entities(daily_wallet: Wallet, long_term_wallet: Wallet) -> tuple[list[Deposit], list[Entity]]:
    """
    Service to create Deposits and Entities for demo User.

    Uses bulk create to create Deposits and Entities at once. Deposits and Entities are returned separately
    for further processing.

    Args:
        daily_wallet (Wallet): "Daily" Wallet instance.
        long_term_wallet (Wallet): "Long term" Wallet instance.

    Returns:
        tuple[list[Deposit], list[Entity]]: Tuple consisting of Deposits and Entities lists.
    """
    deposits_count = 5
    all_entities = Entity.objects.bulk_create(
        [
            # Deposits for "Daily Wallet"
            Entity(
                wallet=daily_wallet,
                name=DepositName.PERSONAL,
                description="Account for personal User expenses and incomes.",
                is_deposit=True,
            ),
            Entity(
                wallet=daily_wallet,
                name=DepositName.COMMON,
                description="Account for common expenses and incomes.",
                is_deposit=True,
            ),
            # Deposits for "Long term" Wallet
            Entity(
                wallet=long_term_wallet,
                name=DepositName.TREASURY_BONDS,
                description="Funds allocated in treasury bonds.",
                is_deposit=True,
            ),
            Entity(
                wallet=long_term_wallet,
                name=DepositName.ETF,
                description="Funds allocated in ETF.",
                is_deposit=True,
            ),
            Entity(
                wallet=long_term_wallet,
                name=DepositName.GOLD,
                description="Funds allocated in gold.",
                is_deposit=True,
            ),
            # Entities for "Daily" Wallet
            Entity(wallet=daily_wallet, name=EntityName.EMPLOYER, description="Employer hiring User."),
            Entity(wallet=daily_wallet, name=EntityName.BUYER, description="Buyer of stuff that User's selling."),
            Entity(wallet=daily_wallet, name=EntityName.FOOD_SELLER, description="Seller that sells food."),
            Entity(wallet=daily_wallet, name=EntityName.BILLS_TAKER, description="Entity that receives bills."),
            Entity(
                wallet=daily_wallet, name=EntityName.UNEXPECTED_ENTITY, description="Entity that charges unexpectedly."
            ),
            Entity(
                wallet=daily_wallet,
                name=EntityName.DAILY_WALLET_TREASURY_BONDS_SELLER,
                description="Entity that sells treasury bonds.",
            ),
            Entity(wallet=daily_wallet, name=EntityName.DAILY_WALLET_ETF_SELLER, description="Entity that sells ETF."),
            Entity(
                wallet=daily_wallet, name=EntityName.DAILY_WALLET_GOLD_SELLER, description="Entity that sells Gold."
            ),
            # Entities for "Long term" Wallet
            Entity(
                wallet=long_term_wallet,
                name=EntityName.LONG_TERM_WALLET_TREASURY_BONDS_SELLER,
                description="Entity that sells treasury bonds.",
            ),
            Entity(
                wallet=long_term_wallet,
                name=EntityName.TREASURY_BONDS_VALUE_CHANGE,
                description="Entity for handling changes of treasury bonds value.",
            ),
            Entity(
                wallet=long_term_wallet,
                name=EntityName.LONG_TERM_WALLET_ETF_SELLER,
                description="Entity that sells ETF.",
            ),
            Entity(
                wallet=long_term_wallet,
                name=EntityName.ETF_VALUE_CHANGE,
                description="Entity for handling changes of ETF value.",
            ),
            Entity(
                wallet=long_term_wallet,
                name=EntityName.LONG_TERM_WALLET_GOLD_SELLER,
                description="Entity that sells Gold.",
            ),
            Entity(
                wallet=long_term_wallet,
                name=EntityName.GOLD_VALUE_CHANGE,
                description="Entity for handling changes of Gold value.",
            ),
        ]
    )
    return all_entities[:deposits_count], all_entities[deposits_count:]
