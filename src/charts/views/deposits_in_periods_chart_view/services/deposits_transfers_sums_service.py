from django.db.models import DecimalField, Sum, Value
from django.db.models.functions import Coalesce

from categories.models.choices.category_type import CategoryType
from transfers.models import Transfer


def get_deposits_transfers_sums_in_period(
    budget_pk: int, deposit_ids: list[int], period: dict, transfer_type: CategoryType
) -> dict[int, float]:
    """
    Calculates passed deposits sum of specified transfer type in given period.

    Args:
        budget_pk (int): Primary key of the budget to filter deposits for
        deposit_ids (list[int]): List of deposit IDs
        period (dict): Period data
        transfer_type (CategoryType): Transfer type

    Returns:
        dict[int, float]: Dict containing deposit id as a key and deposit result as the value.
    """
    period_balances = (
        Transfer.objects.filter(
            deposit_id__in=deposit_ids, period__budget_id=budget_pk, period_id=period["pk"], transfer_type=transfer_type
        )
        .values("deposit_id")
        .annotate(
            deposit_result=Coalesce(
                Sum("value"),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
    )

    return {item["deposit_id"]: float(item["deposit_result"]) for item in period_balances}
