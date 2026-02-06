from datetime import date
from enum import StrEnum
from itertools import chain

from periods.models import Period
from periods.models.choices.period_status import PeriodStatus
from wallets.models import Wallet


class PeriodName(StrEnum):
    _2026_01 = "2026_01"
    _2026_02 = "2026_02"
    _2026_03 = "2026_03"
    _2026_04 = "2026_04"


def create_periods(daily_wallet: Wallet, long_term_wallet: Wallet) -> tuple[list[Period], list[Period]]:
    """
    Service to create Periods for demo User.

    Args:
        daily_wallet (Wallet): "Daily" Wallet instance.
        long_term_wallet (Wallet): "Long term" Wallet instance.

    Returns:
        tuple[list[Period], list[Period]]: Tuple of Periods lists separate to particular Wallet.
    """
    periods_count = 4
    all_periods = Period.objects.bulk_create(
        chain(
            *[
                [
                    Period(
                        wallet=wallet,
                        name=PeriodName._2026_01,
                        date_start=date(2026, 1, 1),
                        date_end=date(2026, 1, 31),
                        status=PeriodStatus.CLOSED,
                    ),
                    Period(
                        wallet=wallet,
                        name=PeriodName._2026_02,
                        date_start=date(2026, 2, 1),
                        date_end=date(2026, 2, 28),
                        status=PeriodStatus.CLOSED,
                    ),
                    Period(
                        wallet=wallet,
                        name=PeriodName._2026_03,
                        date_start=date(2026, 3, 1),
                        date_end=date(2026, 3, 31),
                        status=PeriodStatus.ACTIVE,
                    ),
                    Period(
                        wallet=wallet,
                        name=PeriodName._2026_04,
                        date_start=date(2026, 4, 1),
                        date_end=date(2026, 4, 30),
                        status=PeriodStatus.DRAFT,
                    ),
                ]
                for wallet in [daily_wallet, long_term_wallet]
            ]
        )
    )
    return all_periods[:periods_count], all_periods[periods_count:]
