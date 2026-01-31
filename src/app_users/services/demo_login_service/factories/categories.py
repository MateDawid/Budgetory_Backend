from enum import StrEnum

from app_users.services.demo_login_service.factories.entities import DepositName
from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit


class IncomeCategoryName(StrEnum):
    # Categories for PERSONAL Deposit
    SALARY = "Salary"
    SELL = "Sell"
    # Categories for COMMON Deposit
    FROM_PERSONAL = "Transfers from Personal Account"
    TREASURY_BONDS_SELL = 'Treasury Bonds sell in "Long term" Wallet'
    ETF_SELL = 'ETF sell in "Long term" Wallet'
    GOLD_SELL = 'Gold sell in "Long term" Wallet'
    # Categories for TREASURY_BONDS Deposit
    TREASURY_BONDS_PURCHASE = "Treasury Bonds purchase"
    TREASURY_BONDS_VALUE_INCREASE = "Treasury bonds value increase"
    # Categories for ETF Deposit
    ETF_PURCHASE = "ETF purchase"
    ETF_VALUE_INCREASE = "ETF value increase"
    # Categories for GOLD Deposit
    GOLD_PURCHASE = "Gold purchase"
    GOLD_VALUE_INCREASE = "Gold value increase"


class ExpenseCategoryName(StrEnum):
    # Categories for PERSONAL Deposit
    FOOD = "Food"
    TO_COMMON_ACCOUNT = "Transfer to Common Account Deposit"
    PERSONAL_UNEXPECTED = "Unexpected expenses"
    # Categories for COMMON Deposit
    BILLS = "Bills"
    TREASURY_BONDS_PURCHASE = 'Treasury Bonds purchase in "Long term" Wallet'
    ETF_PURCHASE = 'ETF purchase purchase in "Long term" Wallet'
    GOLD_PURCHASE = 'Gold purchase purchase in "Long term" Wallet'
    COMMON_UNEXPECTED = "Unexpected expenses"
    # Categories for TREASURY_BONDS Deposit
    TREASURY_BONDS_SELL = "Treasury Bonds sell"
    TREASURY_BONDS_VALUE_DECREASE = "Treasury bonds value decrease"
    # Categories for ETF Deposit
    ETF_SELL = "ETF sell"
    ETF_VALUE_DECREASE = "ETF value decrease"
    # Categories for GOLD Deposit
    GOLD_SELL = "Gold sell"
    GOLD_VALUE_DECREASE = "Gold value decrease"


def create_categories(deposits: dict[DepositName, Deposit]) -> tuple[list[TransferCategory], list[TransferCategory]]:
    """
    Service to create Transfer Categories for demo User.

    Uses bulk create to create Income and Expense Categories at once. Both Categories types are returned separately
    for further processing.

    Args:
        deposits (dict[DepositName, Deposit]): Dictionary containing mapping of DepositName to Deposit.

    Returns:
        tuple[list[TransferCategory], list[TransferCategory]]: Tuple consisting of Income and Expense Categories lists.
    """
    income_categories_count = 12
    all_categories = TransferCategory.objects.bulk_create(
        [
            # Income Categories for PERSONAL Deposit
            TransferCategory(
                name=IncomeCategoryName.SALARY,
                description="Monthly salary.",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.REGULAR,
                deposit=deposits[DepositName.PERSONAL],
                wallet=deposits[DepositName.PERSONAL].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.SELL,
                description="Cash earned from selling stuff.",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.PERSONAL],
                wallet=deposits[DepositName.PERSONAL].wallet,
            ),
            # Income Categories for COMMON Deposit
            TransferCategory(
                name=IncomeCategoryName.FROM_PERSONAL,
                description="Monthly transfer from Personal Account.",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.REGULAR,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.TREASURY_BONDS_SELL,
                description='Treasury bonds sell in "Long term" Wallet.',
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.ETF_SELL,
                description='ETF sell in "Long term" Wallet.',
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.GOLD_SELL,
                description='Gold sell in "Long term" Wallet.',
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            # Income Categories for TREASURY_BONDS Deposit
            TransferCategory(
                name=IncomeCategoryName.TREASURY_BONDS_PURCHASE,
                description="Purchase of Treasury Bonds",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.TREASURY_BONDS],
                wallet=deposits[DepositName.TREASURY_BONDS].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.TREASURY_BONDS_VALUE_INCREASE,
                description="Value increase of Treasury Bonds",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.REGULAR,
                deposit=deposits[DepositName.TREASURY_BONDS],
                wallet=deposits[DepositName.TREASURY_BONDS].wallet,
            ),
            # Income Categories for ETF Deposit
            TransferCategory(
                name=IncomeCategoryName.ETF_PURCHASE,
                description="Purchase of ETF",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.ETF],
                wallet=deposits[DepositName.ETF].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.ETF_VALUE_INCREASE,
                description="Value increase of ETF",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.REGULAR,
                deposit=deposits[DepositName.ETF],
                wallet=deposits[DepositName.ETF].wallet,
            ),
            # Income Categories for GOLD Deposit
            TransferCategory(
                name=IncomeCategoryName.GOLD_PURCHASE,
                description="Purchase of Gold",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.IRREGULAR,
                deposit=deposits[DepositName.GOLD],
                wallet=deposits[DepositName.GOLD].wallet,
            ),
            TransferCategory(
                name=IncomeCategoryName.GOLD_VALUE_INCREASE,
                description="Value increase of Gold",
                category_type=CategoryType.INCOME,
                priority=CategoryPriority.REGULAR,
                deposit=deposits[DepositName.GOLD],
                wallet=deposits[DepositName.GOLD].wallet,
            ),
            # Expense categories for PERSONAL Deposit
            TransferCategory(
                name=ExpenseCategoryName.FOOD,
                description="Food expenses",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.MOST_IMPORTANT,
                deposit=deposits[DepositName.PERSONAL],
                wallet=deposits[DepositName.PERSONAL].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.TO_COMMON_ACCOUNT,
                description="Transfer to Common Account for common monthly expenses.",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.MOST_IMPORTANT,
                deposit=deposits[DepositName.PERSONAL],
                wallet=deposits[DepositName.PERSONAL].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.PERSONAL_UNEXPECTED,
                description="Unexpected expenses.",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.PERSONAL],
                wallet=deposits[DepositName.PERSONAL].wallet,
            ),
            # Expense categories for COMMON Deposit
            TransferCategory(
                name=ExpenseCategoryName.BILLS,
                description="Bills expenses.",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.MOST_IMPORTANT,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.TREASURY_BONDS_PURCHASE,
                description='Treasury Bonds purchase in "Long term" Wallet',
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.SAVINGS,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.ETF_PURCHASE,
                description='ETF purchase in "Long term" Wallet',
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.SAVINGS,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.GOLD_PURCHASE,
                description='Gold purchase in "Long term" Wallet',
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.SAVINGS,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.COMMON_UNEXPECTED,
                description="Unexpected expenses.",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.COMMON],
                wallet=deposits[DepositName.COMMON].wallet,
            ),
            # Expense categories for TREASURY_BONDS Deposit
            TransferCategory(
                name=ExpenseCategoryName.TREASURY_BONDS_SELL,
                description="Treasury Bonds sell",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.TREASURY_BONDS],
                wallet=deposits[DepositName.TREASURY_BONDS].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.TREASURY_BONDS_VALUE_DECREASE,
                description="Treasury Bonds value decrease",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.TREASURY_BONDS],
                wallet=deposits[DepositName.TREASURY_BONDS].wallet,
            ),
            # Expense categories for ETF Deposit
            TransferCategory(
                name=ExpenseCategoryName.ETF_SELL,
                description="ETF sell",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.ETF],
                wallet=deposits[DepositName.ETF].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.ETF_VALUE_DECREASE,
                description="ETF value decrease",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.ETF],
                wallet=deposits[DepositName.ETF].wallet,
            ),
            # Expense categories for GOLD Deposit
            TransferCategory(
                name=ExpenseCategoryName.GOLD_SELL,
                description="Gold sell",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.GOLD],
                wallet=deposits[DepositName.GOLD].wallet,
            ),
            TransferCategory(
                name=ExpenseCategoryName.GOLD_VALUE_DECREASE,
                description="Gold value decrease",
                category_type=CategoryType.EXPENSE,
                priority=CategoryPriority.OTHERS,
                deposit=deposits[DepositName.GOLD],
                wallet=deposits[DepositName.GOLD].wallet,
            ),
        ]
    )
    return all_categories[:income_categories_count], all_categories[income_categories_count:]
