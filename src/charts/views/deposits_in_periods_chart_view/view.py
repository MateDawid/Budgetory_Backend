from functools import partial
from typing import Any

from django.db.models import Subquery
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from categories.models.choices.category_type import CategoryType
from charts.views.deposits_in_periods_chart_view.services.deposits_balances_service import (
    get_deposits_balance_in_period,
)
from charts.views.deposits_in_periods_chart_view.services.deposits_transfers_sums_service import (
    get_deposits_transfers_sums_in_period,
)
from entities.models import Deposit


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


def get_deposits(budget_pk: int, deposit_id: str) -> list[dict[str, Any]]:
    """
    Retrieve deposits for a specific budget with optional filtering.

    Filters deposits based on budget ID and optional deposit type or specific deposit ID
    from the query parameters. Results are ordered by deposit type and name for consistent output.

    Args:
        budget_pk (int): Primary key of the budget to filter deposits for
        deposit_id (str): Specific deposit ID to filter by

    Returns:
        List[dict[str, Any]]: List of deposit dictionaries containing:
            - pk: Deposit primary key
            - name: Deposit name
    """
    query_filters: dict = {"budget_id": budget_pk}
    if deposit_id:
        query_filters["id"] = deposit_id
    return list(Deposit.objects.filter(**query_filters).order_by("deposit_type", "name").values("pk", "name"))


def get_chart_data(
    deposits: list[dict[str, Any]], all_deposits_results: list[dict[str, Any]], display_value: CategoryType | None
) -> list[dict[str, Any]]:
    """
    Coverts deposits balances date to MUI charts format.

    Args:
        deposits (list[dict[str, Any]]): Deposits data.
        all_deposits_results(list[dict[str, Any]]): All Deposits results in periods.
        display_value (CategoryType|None): Type of value to display on chart.
    Returns:
        list[dict[str, Any]]: Formatted deposits balances in periods.
    """
    deposits_count = len(deposits)
    series_data = []
    for idx, deposit in enumerate(deposits):
        deposit_id = deposit["pk"]
        deposit_results = [item["results"] for item in all_deposits_results if item["deposit_id"] == deposit_id]
        series_data.append(
            {
                "label": deposit["name"],
                "data": deposit_results,
                "color": generate_rgba_value(idx, deposits_count, display_value),
            }
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
        # Filter out periods
        periods = get_periods(budget_pk=budget_pk, query_params=request.query_params)
        if not periods:
            return Response({"xAxis": [], "series": []})
        # Filter out deposits
        deposits = get_deposits(budget_pk=budget_pk, deposit_id=request.query_params.get("deposit"))
        if not deposits:
            return Response({"xAxis": [], "series": []})
        # Select proper service chart data generation
        deposits_ids = [deposit["pk"] for deposit in deposits]
        if display_value := request.query_params.get("display_value"):
            chart_data_service = partial(
                get_deposits_transfers_sums_in_period,
                budget_pk=budget_pk,
                deposit_ids=deposits_ids,
                transfer_type=display_value,
            )
        else:
            chart_data_service = partial(get_deposits_balance_in_period, budget_pk=budget_pk, deposit_ids=deposits_ids)

        # Get chart data
        formatted_deposits_results: list[dict[str, Any]] = []

        for period in periods:
            all_deposits_results: dict[int, float] = chart_data_service(period=period)
            for deposit in deposits:
                deposit_results = all_deposits_results.get(deposit["pk"], 0.0)
                formatted_deposits_results.append(
                    {
                        "deposit_id": deposit["pk"],
                        "deposit_name": deposit["name"],
                        "period_name": period["name"],
                        "results": deposit_results,
                    }
                )

        series_data: list[dict[str, Any]] = get_chart_data(
            deposits=deposits, all_deposits_results=formatted_deposits_results, display_value=display_value
        )

        return Response({"xAxis": [period["name"] for period in periods], "series": series_data})
