from functools import partial
from typing import Any

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.models.choices.category_type import CategoryType
from charts.views.deposits_in_periods_chart_view.services.deposits_balances_service import (
    get_deposits_balance_in_period,
)
from charts.views.deposits_in_periods_chart_view.services.deposits_transfers_sums_service import (
    get_deposits_transfers_sums_in_period,
)
from charts.views.utils import generate_rgba_value, get_periods
from entities.models import Deposit


def get_deposits(wallet_pk: int, deposit_id: str) -> list[dict[str, Any]]:
    """
    Retrieve deposits for a specific wallet with optional filtering.

    Filters deposits based on wallet ID and optional deposit type or specific deposit ID
    from the query parameters. Results are ordered by deposit type and name for consistent output.

    Args:
        wallet_pk (int): Primary key of the wallet to filter deposits for
        deposit_id (str): Specific deposit ID to filter by

    Returns:
        List[dict[str, Any]]: List of deposit dictionaries containing:
            - pk: Deposit primary key
            - name: Deposit name
    """
    query_filters: dict = {"wallet_id": wallet_pk}
    if deposit_id:
        query_filters["id"] = deposit_id
    return list(Deposit.objects.filter(**query_filters).order_by("name").values("pk", "name"))


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
        - User must belong to the specified wallet

    Query Parameters:
        - period_from (optional): Starting period ID for date range filtering
        - period_to (optional): Ending period ID for date range filtering
        - deposit (optional): Filter to specific deposit ID

    Returns:
        Response containing:
            - xAxis: List of period names for chart x-axis
            - series: List of deposit series data with labels, balance data, and colors
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToWalletPermission,
    )

    def get(self, request: Request, wallet_pk: int, **kwargs: dict[str, Any]) -> Response:
        """
        Handle GET requests for deposit balance results.

        Retrieves and processes deposit balance data across specified periods,
        calculating cumulative balances for each deposit and formatting the results
        for chart visualization.

        Args:
            request (Request): DRF request object containing query parameters
            wallet_pk (int): Primary key of the wallet to analyze
            **kwargs (dict[str, Any]): Additional keyword arguments from URL routing

        Returns:
            Response: JSON response containing chart data with xAxis (period names)
                     and series (deposit balance data with colors)
        """
        # Filter out periods
        periods = get_periods(wallet_pk=wallet_pk, query_params=request.query_params)
        if not periods:
            return Response({"xAxis": [], "series": []})
        # Filter out deposits
        deposits = get_deposits(wallet_pk=wallet_pk, deposit_id=request.query_params.get("deposit"))
        if not deposits:
            return Response({"xAxis": [], "series": []})
        # Select proper service chart data generation
        deposits_ids = [deposit["pk"] for deposit in deposits]
        if display_value := request.query_params.get("display_value"):
            chart_data_service = partial(
                get_deposits_transfers_sums_in_period,
                wallet_pk=wallet_pk,
                deposit_ids=deposits_ids,
                transfer_type=display_value,
            )
        else:
            chart_data_service = partial(get_deposits_balance_in_period, wallet_pk=wallet_pk, deposit_ids=deposits_ids)

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
