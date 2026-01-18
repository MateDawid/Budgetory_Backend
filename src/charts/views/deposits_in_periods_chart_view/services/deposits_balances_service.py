from django.db.models import Case, DecimalField, F, Sum, Value, When
from django.db.models.functions import Coalesce

from categories.models.choices.category_type import CategoryType
from transfers.models import Transfer


def get_deposits_balance_in_period(wallet_pk: int, deposit_ids: list[int], period: dict) -> dict[int, float]:
    """
    Calculates passed deposits balances at the end of period.

    Args:
        wallet_pk (int): Primary key of the wallet to filter deposits for
        deposit_ids (list[int]): List of deposit IDs
        period (dict): Period data

    Returns:
        dict[int, float]: Dict containing deposit id as a key and deposit balance as the value.
    """
    period_balances = (
        Transfer.objects.filter(
            deposit_id__in=deposit_ids, period__wallet_id=wallet_pk, period__date_end__lte=period["date_end"]
        )
        .values("deposit_id")
        .annotate(
            balance=Coalesce(
                Sum(
                    Case(
                        When(transfer_type=CategoryType.INCOME, then=F("value")),
                        When(transfer_type=CategoryType.EXPENSE, then=-F("value")),
                        default=Value(0),
                        output_field=DecimalField(max_digits=10, decimal_places=2),
                    )
                ),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
    )

    return {item["deposit_id"]: float(item["balance"]) for item in period_balances}
