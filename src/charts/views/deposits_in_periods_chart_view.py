from typing import Any

from django.db.models import Case, DecimalField, F, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce
from django.utils.datetime_safe import datetime
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from transfers.models import Transfer


def generate_red_color(index: int, total_count: int) -> str:
    """
    Generate red color based on index in the range (80-255).
    RED min value 80, max value 255.

    Args:
        index (int): Current series index
        total_count (int): Total number of series

    Returns:
        str: RGBA color string
    """
    max_value = 255
    min_value = 80
    red_value = int((((max_value - min_value) / total_count) * index) + 80)
    return f"rgba({red_value}, 0, 0, 1)"


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
    query_filters = {"budget_id": budget_pk}
    if period_from_id := query_params.get("period_from"):
        query_filters["date_start__gte"] = Subquery(
            BudgetingPeriod.objects.filter(pk=period_from_id).values("date_start")[:1]
        )
    if period_to_id := query_params.get("period_to"):
        query_filters["date_end__lte"] = Subquery(
            BudgetingPeriod.objects.filter(pk=period_to_id).values("date_end")[:1]
        )
    return list(BudgetingPeriod.objects.filter(**query_filters).order_by("date_start").values("pk", "name", "date_end"))


def get_deposits(budget_pk: int, query_params: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Retrieve deposits for a specific budget with optional filtering.

    Filters deposits based on budget ID and optional deposit type or specific deposit ID
    from the query parameters. Results are ordered by deposit type and name for consistent output.

    Args:
        budget_pk (int): Primary key of the budget to filter deposits for
        query_params (dict[str, Any]): Query parameters dictionary containing optional filters:
            - deposit_type: Type of deposit to filter by
            - deposit: Specific deposit ID to filter by

    Returns:
        List[dict[str, Any]]: List of deposit dictionaries containing:
            - pk: Deposit primary key
            - name: Deposit name
    """
    query_filters = {"budget_id": budget_pk}
    if deposit_type := query_params.get("deposit_type"):
        query_filters["deposit_type"] = deposit_type
    if deposit_id := query_params.get("deposit"):
        query_filters["id"] = deposit_id
    return list(Deposit.objects.filter(**query_filters).order_by("deposit_type", "name").values("pk", "name"))


def get_deposits_balances_in_period(
    budget_pk: int, deposit_ids: list[int], period_date_end: datetime.date
) -> dict[int, float]:
    """
    Calculates passed deposits balances at the end of period.

    Args:
        budget_pk (int): Primary key of the budget to filter deposits for
        deposit_ids (list[int]): List of deposit IDs
        period_date_end (datetime.date): Period end date

    Returns:
        dict[int, float]: Dict containing deposit id as a key and deposit balance as the value.
    """
    period_balances = (
        Transfer.objects.filter(
            deposit_id__in=deposit_ids, period__budget_id=budget_pk, period__date_end__lte=period_date_end
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


def get_chart_data(deposits: list[dict[str, Any]], balances_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Coverts deposits balances date to MUI charts format.

    Args:
        deposits (list[dict[str, Any]]): Deposits data.
        balances_data(list[dict[str, Any]]): Deposits balances data in periods.
    Returns:
        list[dict[str, Any]]: Formatted deposits balances in periods.
    """
    deposits_count = len(deposits)
    series_data = []
    for idx, deposit in enumerate(deposits):
        deposit_id = deposit["pk"]
        balances = [item["balance"] for item in balances_data if item["deposit_id"] == deposit_id]

        series_data.append(
            {"label": deposit["name"], "data": balances, "color": generate_red_color(idx, deposits_count)}
        )
    return series_data


class DepositsInPeriodsChartAPIView(APIView):
    """
    API view for retrieving deposit balance results across multiple periods.

    Permissions:
        - User must be authenticated
        - User must belong to the specified budget

    Query Parameters:
        - period_from (optional): Starting period ID for date range filtering
        - period_to (optional): Ending period ID for date range filtering
        - deposit_type (optional): Filter deposits by type
        - deposit (optional): Filter to specific deposit ID

    Returns:
        Response containing:
            - xAxis: List of period names for chart x-axis
            - series: List of deposit series data with labels, balance data, and colors
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def get(self, request: Request, budget_pk: int, **kwargs: dict[str, Any]) -> Response:
        """
        Handle GET requests for deposit balance results.

        Retrieves and processes deposit balance data across specified periods,
        calculating cumulative balances for each deposit and formatting the results
        for chart visualization.

        Args:
            request (Request): DRF request object containing query parameters
            budget_pk (int): Primary key of the budget to analyze
            **kwargs (dict[str, Any]): Additional keyword arguments from URL routing

        Returns:
            Response: JSON response containing chart data with xAxis (period names)
                     and series (deposit balance data with colors)
        """
        query_params = request.query_params.dict()

        periods = get_periods(budget_pk, query_params)
        if not periods:
            return Response({"xAxis": [], "series": []})

        deposits = get_deposits(budget_pk, query_params)
        if not deposits:
            return Response({"xAxis": [], "series": []})

        balances_data: list[dict[str, Any]] = []

        for period in periods:
            balance_dict: dict[int, float] = get_deposits_balances_in_period(
                budget_pk=budget_pk,
                deposit_ids=[deposit["pk"] for deposit in deposits],
                period_date_end=period["date_end"],
            )

            for deposit in deposits:
                balance = balance_dict.get(deposit["pk"], 0.0)
                balances_data.append(
                    {
                        "deposit_id": deposit["pk"],
                        "deposit_name": deposit["name"],
                        "period_name": period["name"],
                        "balance": balance,
                    }
                )

        series_data: list[dict[str, Any]] = get_chart_data(deposits=deposits, balances_data=balances_data)

        return Response({"xAxis": [period["name"] for period in periods], "series": series_data})
