from datetime import date
from decimal import Decimal

from app_users.services.demo_login_service.factories.categories import IncomeCategoryName
from app_users.services.demo_login_service.factories.entities import DepositName, EntityName
from app_users.services.demo_login_service.factories.periods import PeriodName
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit, Entity
from periods.models import Period
from transfers.models import Income


def create_incomes(
    daily_wallet_periods: dict[PeriodName, Period],
    long_term_wallet_periods: dict[PeriodName, Period],
    deposits: dict[DepositName, Deposit],
    entities: dict[EntityName, Entity],
    income_categories: dict[IncomeCategoryName, TransferCategory],
) -> None:
    """
    Service to create Incomes for demo User.
    """
    ...
    Income.objects.bulk_create(
        [
            # DAILY Wallet PERSONAL Deposit 2026_01 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2026, 1, 1),
                period=daily_wallet_periods[PeriodName._2026_01],
                value=Decimal("6200.00"),
                deposit=deposits[DepositName.PERSONAL],
                entity=entities[EntityName.EMPLOYER],
                category=income_categories[IncomeCategoryName.SALARY],
                description="Salary for 2025.12",
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Sell",
                date=date(2026, 1, 20),
                period=daily_wallet_periods[PeriodName._2026_01],
                value=Decimal("200.00"),
                deposit=deposits[DepositName.PERSONAL],
                entity=entities[EntityName.BUYER],
                category=income_categories[IncomeCategoryName.SELL],
                description="Selling stuff",
            ),
            # DAILY Wallet PERSONAL Deposit 2026_02 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2026, 2, 1),
                period=daily_wallet_periods[PeriodName._2026_02],
                value=Decimal("6200.00"),
                deposit=deposits[DepositName.PERSONAL],
                entity=entities[EntityName.EMPLOYER],
                category=income_categories[IncomeCategoryName.SALARY],
                description="Salary for 2026.01",
            ),
            # DAILY Wallet PERSONAL Deposit 2026_03 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Salary",
                date=date(2026, 3, 1),
                period=daily_wallet_periods[PeriodName._2026_03],
                value=Decimal("6700.00"),
                deposit=deposits[DepositName.PERSONAL],
                entity=entities[EntityName.EMPLOYER],
                category=income_categories[IncomeCategoryName.SALARY],
                description="Salary for 2025.12",
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Sell",
                date=date(2026, 3, 10),
                period=daily_wallet_periods[PeriodName._2026_03],
                value=Decimal("100.00"),
                deposit=deposits[DepositName.PERSONAL],
                entity=entities[EntityName.BUYER],
                category=income_categories[IncomeCategoryName.SELL],
                description="Selling stuff",
            ),
            # DAILY Wallet COMMON Deposit 2026_01 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="From Personal Account",
                date=date(2026, 1, 1),
                period=daily_wallet_periods[PeriodName._2026_01],
                value=Decimal("5000.00"),
                deposit=deposits[DepositName.COMMON],
                entity=deposits[DepositName.PERSONAL],
                category=income_categories[IncomeCategoryName.FROM_PERSONAL],
            ),
            # DAILY Wallet COMMON Deposit 2026_02 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="From Personal Account",
                date=date(2026, 2, 1),
                period=daily_wallet_periods[PeriodName._2026_02],
                value=Decimal("5000.00"),
                deposit=deposits[DepositName.COMMON],
                entity=deposits[DepositName.PERSONAL],
                category=income_categories[IncomeCategoryName.FROM_PERSONAL],
            ),
            # DAILY Wallet COMMON Deposit 2026_03 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="From Personal Account",
                date=date(2026, 3, 1),
                period=daily_wallet_periods[PeriodName._2026_03],
                value=Decimal("5500.00"),
                deposit=deposits[DepositName.COMMON],
                entity=deposits[DepositName.PERSONAL],
                category=income_categories[IncomeCategoryName.FROM_PERSONAL],
            ),
            # LONG TERM Wallet TREASURY_BONDS Deposit 2026_01 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds purchase",
                date=date(2026, 1, 1),
                period=long_term_wallet_periods[PeriodName._2026_01],
                value=Decimal("1000.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.LONG_TERM_WALLET_TREASURY_BONDS_SELLER],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_PURCHASE],
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds value increase",
                date=date(2026, 1, 1),
                period=long_term_wallet_periods[PeriodName._2026_01],
                value=Decimal("10.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.TREASURY_BONDS_VALUE_CHANGE],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_VALUE_INCREASE],
            ),
            # LONG TERM Wallet TREASURY_BONDS Deposit 2026_02 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds purchase",
                date=date(2026, 2, 1),
                period=long_term_wallet_periods[PeriodName._2026_02],
                value=Decimal("1000.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.LONG_TERM_WALLET_TREASURY_BONDS_SELLER],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_PURCHASE],
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds value increase",
                date=date(2026, 2, 1),
                period=long_term_wallet_periods[PeriodName._2026_02],
                value=Decimal("10.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.TREASURY_BONDS_VALUE_CHANGE],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_VALUE_INCREASE],
            ),
            # LONG TERM Wallet TREASURY_BONDS Deposit 2026_03 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds purchase",
                date=date(2026, 3, 1),
                period=long_term_wallet_periods[PeriodName._2026_03],
                value=Decimal("1250.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.LONG_TERM_WALLET_TREASURY_BONDS_SELLER],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_PURCHASE],
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Treasury Bonds value increase",
                date=date(2026, 3, 1),
                period=long_term_wallet_periods[PeriodName._2026_03],
                value=Decimal("10.00"),
                deposit=deposits[DepositName.TREASURY_BONDS],
                entity=entities[EntityName.TREASURY_BONDS_VALUE_CHANGE],
                category=income_categories[IncomeCategoryName.TREASURY_BONDS_VALUE_INCREASE],
            ),
            # LONG TERM Wallet ETF Deposit 2026_01 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="ETF purchase",
                date=date(2026, 1, 1),
                period=long_term_wallet_periods[PeriodName._2026_01],
                value=Decimal("1000.00"),
                deposit=deposits[DepositName.ETF],
                entity=entities[EntityName.LONG_TERM_WALLET_ETF_SELLER],
                category=income_categories[IncomeCategoryName.ETF_PURCHASE],
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="ETF value increase",
                date=date(2026, 1, 1),
                period=long_term_wallet_periods[PeriodName._2026_01],
                value=Decimal("100.00"),
                deposit=deposits[DepositName.ETF],
                entity=entities[EntityName.ETF_VALUE_CHANGE],
                category=income_categories[IncomeCategoryName.ETF_VALUE_INCREASE],
            ),
            # LONG TERM Wallet ETF Deposit 2026_02 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="ETF purchase",
                date=date(2026, 2, 1),
                period=long_term_wallet_periods[PeriodName._2026_02],
                value=Decimal("1000.00"),
                deposit=deposits[DepositName.ETF],
                entity=entities[EntityName.LONG_TERM_WALLET_ETF_SELLER],
                category=income_categories[IncomeCategoryName.ETF_PURCHASE],
            ),
            # LONG TERM Wallet ETF Deposit 2026_03 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="ETF purchase",
                date=date(2026, 3, 1),
                period=long_term_wallet_periods[PeriodName._2026_03],
                value=Decimal("1250.00"),
                deposit=deposits[DepositName.ETF],
                entity=entities[EntityName.LONG_TERM_WALLET_ETF_SELLER],
                category=income_categories[IncomeCategoryName.ETF_PURCHASE],
            ),
            # LONG TERM Wallet GOLD Deposit 2026_01 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Gold purchase",
                date=date(2026, 1, 1),
                period=long_term_wallet_periods[PeriodName._2026_01],
                value=Decimal("500.00"),
                deposit=deposits[DepositName.GOLD],
                entity=entities[EntityName.LONG_TERM_WALLET_GOLD_SELLER],
                category=income_categories[IncomeCategoryName.GOLD_PURCHASE],
            ),
            # LONG TERM Wallet ETF Deposit 2026_02 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Gold purchase",
                date=date(2026, 2, 1),
                period=long_term_wallet_periods[PeriodName._2026_02],
                value=Decimal("500.00"),
                deposit=deposits[DepositName.GOLD],
                entity=entities[EntityName.LONG_TERM_WALLET_GOLD_SELLER],
                category=income_categories[IncomeCategoryName.GOLD_PURCHASE],
            ),
            # LONG TERM Wallet GOLD Deposit 2026_03 Incomes
            Income(
                transfer_type=CategoryType.INCOME,
                name="Gold purchase",
                date=date(2026, 3, 1),
                period=long_term_wallet_periods[PeriodName._2026_03],
                value=Decimal("500.00"),
                deposit=deposits[DepositName.GOLD],
                entity=entities[EntityName.LONG_TERM_WALLET_GOLD_SELLER],
                category=income_categories[IncomeCategoryName.GOLD_PURCHASE],
            ),
            Income(
                transfer_type=CategoryType.INCOME,
                name="Gold value increase",
                date=date(2026, 3, 1),
                period=long_term_wallet_periods[PeriodName._2026_03],
                value=Decimal("20.00"),
                deposit=deposits[DepositName.GOLD],
                entity=entities[EntityName.GOLD_VALUE_CHANGE],
                category=income_categories[IncomeCategoryName.GOLD_VALUE_INCREASE],
            ),
        ]
    )
