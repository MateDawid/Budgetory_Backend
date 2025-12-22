# TODO: Chart utils
from typing import Any

from django.db.models import Subquery

from budgets.models import BudgetingPeriod
from categories.models.choices.category_type import CategoryType


def generate_rgba_value(index: int, total_count: int, display_value: CategoryType | None) -> str:
    """
    Generate color based on index in the range (80-255).
    RED/GREEN min value 80, max value 255.

    Args:
        index (int): Current series index
        total_count (int): Total number of series
        display_value (CategoryType|None): Type of value to display on chart.

    Returns:
        str: RGBA color string
    """
    max_value = 255
    min_value = 80
    color_value = int((((max_value - min_value) / total_count) * index) + 80)
    if display_value == str(CategoryType.EXPENSE.value):
        return f"rgba({color_value}, 0, 0, 1)"
    elif display_value == str(CategoryType.INCOME.value):
        return f"rgba(0, {color_value}, 0, 1)"
    else:
        color_value = color_value / max_value
        return f"rgba(0, 0, 0, {color_value})"


def get_periods(budget_pk: int, query_params: dict[str, str]) -> list[dict[str, Any]]:
    """
    Retrieve budgeting periods for a specific budget with optional date filtering.

    Filters periods based on budget ID and optional date range constraints using
    period_from and period_to query parameters.

    Args:
        budget_pk (int): Primary key of the budget to filter periods for
        query_params (dict[str, str]): Query parameters dictionary containing optional filters:
            - period_from: ID of the starting period for date range filtering
            - period_to: ID of the ending period for date range filtering

    Returns:
        List[dict[str, Any]]: List of period dictionaries containing:
            - pk: Period primary key
            - name: Period name
            - date_end: Period end date
    """
    query_filters: dict = {"budget_id": budget_pk}
    if period_from_id := query_params.get("period_from"):
        query_filters["date_start__gte"] = Subquery(
            BudgetingPeriod.objects.filter(pk=period_from_id).values("date_start")[:1]
        )
    if period_to_id := query_params.get("period_to"):
        query_filters["date_end__lte"] = Subquery(
            BudgetingPeriod.objects.filter(pk=period_to_id).values("date_end")[:1]
        )
    return list(BudgetingPeriod.objects.filter(**query_filters).order_by("date_start").values("pk", "name", "date_end"))
