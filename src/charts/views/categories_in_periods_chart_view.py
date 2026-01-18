from functools import partial
from typing import Any

from django.db.models import DecimalField, F, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from charts.views.utils import generate_rgba_value, get_periods
from transfers.models import Transfer


def get_categories(wallet_pk: int, category_id: str, category_type: str, deposit_id: str) -> list[dict[str, Any]]:
    """
    Retrieve categories for a specific wallet with optional filtering.

    Filters categories based on wallet ID or specific category ID
    from the query parameters. Results are ordered by priority and name for consistent output.

    Args:
        wallet_pk (int): Primary key of the wallet to filter categories for
        category_id (str): Specific category ID to filter by
        category_type (str): Category type (Expense or Income)
        deposit_id (str): Deposit ID to filter by

    Returns:
        List[dict[str, Any]]: List of category dictionaries containing:
            - pk: Category primary key
            - name: Category name
    """
    query_filters: dict = {"wallet_id": wallet_pk}
    if category_id:
        query_filters["id"] = category_id
    if category_type:
        query_filters["category_type"] = category_type
    if deposit_id:
        query_filters["deposit_id"] = deposit_id
    return list(
        TransferCategory.objects.filter(**query_filters)
        .annotate(deposit_name=F("deposit__name"))
        .order_by("deposit_name", "category_type", "priority", "name")
        .values("pk", "name", "deposit_name")
    )


def get_chart_data(
    categories: list[dict[str, Any]], all_categories_results: list[dict[str, Any]], category_type: CategoryType | None
) -> list[dict[str, Any]]:
    """
    Coverts categories balances date to MUI charts format.

    Args:
        categories (list[dict[str, Any]]): Categories data.
        all_categories_results(list[dict[str, Any]]): All Categories results in periods.
        category_type (CategoryType|None): CategoryType (Expense or Income).
    Returns:
        list[dict[str, Any]]: Formatted categories balances in periods.
    """
    categories_count = len(categories)
    series_data = []
    for idx, category in enumerate(categories):
        category_id = category["pk"]
        category_results = [item["results"] for item in all_categories_results if item["category_id"] == category_id]
        series_data.append(
            {
                "label": f'({category["deposit_name"]}) {category["name"]}',
                "data": category_results,
                "color": generate_rgba_value(idx, categories_count, category_type),
            }
        )
    return series_data


def get_categories_transfers_sums_in_period(
    wallet_pk: int, categories_ids: list[int], period: dict
) -> dict[int, float]:
    """
    Calculates passed transfer categories sum of specified in given period.

    Args:
        wallet_pk (int): Primary key of the wallet to filter categories for
        categories_ids (list[int]): List of TransferCategory IDs
        period (dict): Period data

    Returns:
        dict[int, float]: Dict containing category id as a key and category result as the value.
    """
    period_results = (
        Transfer.objects.filter(category_id__in=categories_ids, period__wallet_id=wallet_pk, period_id=period["pk"])
        .values("category_id")
        .annotate(
            result=Coalesce(
                Sum("value"),
                Value(0, output_field=DecimalField(max_digits=10, decimal_places=2)),
            )
        )
    )

    return {item["category_id"]: float(item["result"]) for item in period_results}


class CategoriesInPeriodsChartAPIView(APIView):
    """
    API view for retrieving category balance results across multiple periods.

    Permissions:
        - User must be authenticated
        - User must belong to the specified wallet

    Query Parameters:
        - period_from (optional): Starting period ID for date range filtering
        - period_to (optional): Ending period ID for date range filtering
        - category_type (optional): Filter categories by type
        - category (optional): Filter to specific category ID

    Returns:
        Response containing:
            - xAxis: List of period names for chart x-axis
            - series: List of category series data with labels, balance data, and colors
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToWalletPermission,
    )

    def get(self, request: Request, wallet_pk: int, **kwargs: dict[str, Any]) -> Response:
        """
        Handle GET requests for category balance results.

        Retrieves and processes category balance data across specified periods,
        calculating cumulative balances for each category and formatting the results
        for chart visualization.

        Args:
            request (Request): DRF request object containing query parameters
            wallet_pk (int): Primary key of the wallet to analyze
            **kwargs (dict[str, Any]): Additional keyword arguments from URL routing

        Returns:
            Response: JSON response containing chart data with xAxis (period names)
                     and series (category balance data with colors)
        """
        # Filter out periods
        periods = get_periods(wallet_pk=wallet_pk, query_params=request.query_params)
        if not periods:
            return Response({"xAxis": [], "series": []})
        # Filter out categories
        category_type = request.query_params.get("category_type")
        categories = get_categories(
            wallet_pk=wallet_pk,
            category_id=request.query_params.get("category"),
            category_type=category_type,
            deposit_id=request.query_params.get("deposit"),
        )
        if not categories:
            return Response({"xAxis": [], "series": []})
        # Prepare service for chart data generation
        chart_data_service = partial(
            get_categories_transfers_sums_in_period,
            wallet_pk=wallet_pk,
            categories_ids=[category["pk"] for category in categories],
        )

        # Get chart data
        formatted_categories_results: list[dict[str, Any]] = []

        for period in periods:
            all_categories_results: dict[int, float] = chart_data_service(period=period)
            for category in categories:
                category_results = all_categories_results.get(category["pk"], 0.0)
                formatted_categories_results.append(
                    {
                        "category_id": category["pk"],
                        "category_name": category["name"],
                        "period_name": period["name"],
                        "results": category_results,
                    }
                )

        series_data: list[dict[str, Any]] = get_chart_data(
            categories=categories, all_categories_results=formatted_categories_results, category_type=category_type
        )

        return Response({"xAxis": [period["name"] for period in periods], "series": series_data})
