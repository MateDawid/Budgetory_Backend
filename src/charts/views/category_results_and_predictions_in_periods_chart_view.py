from enum import Enum
from functools import partial

from django.db.models import DecimalField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from predictions.models import ExpensePrediction
from transfers.models import Transfer


class DisplayValueChoices(Enum):
    RESULTS = 1
    PREDICTIONS = 2


def get_period_transfers_sum_in_category(category_id: str) -> Coalesce:
    """
    Calculates sum of given TransferCategory Transfers in Period.

    Args:
        category_id (str | None): Deposit ID or None.
    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    return Coalesce(
        Subquery(
            Transfer.objects.filter(Q(period_id=OuterRef("id"), category_id=category_id))
            .values("period")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def get_period_predictions_for_category(category_id: str) -> Coalesce:
    """
    Calculates sum of given TransferCategory Transfers in Period.

    Args:
        category_id (str | None): Deposit ID or None.
    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    return Coalesce(
        Subquery(
            ExpensePrediction.objects.filter(
                period_id=OuterRef("id"),
                category_id=category_id,
            ).values(
                "current_plan"
            )[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class CategoryResultsAndPredictionsInPeriodsChartApiView(APIView):
    """
    API view for retrieving data about TransferCategory Transfers sum and Predictions in Periods for chart purposes.

    Returns:
        Response containing:
            - xAxis: List of Period names for chart x-axis
            - results_series: List of accumulated Expenses for TransferCategory in Periods.
            - predictions_series: List of ExpensePrediction current_plan values for TransferCategory values in Periods.
    """

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def get(self, request: Request, budget_pk: int) -> Response:
        """
        Handle GET requests for Period Transfers chart data.

        Args:
            request (Request): User Request.
            budget_pk (int): Budget PK.

        Returns:
            Response: JSON response containing chart data with xAxis (period names),
            expense_series (accumulated Expenses from all Deposits in Periods) and income_series
            (accumulated Incomes from all Deposits in Periods).
        """
        # Query params
        category_id = request.query_params.get("category", None)
        display_value = request.query_params.get("display_value", None)
        if not category_id:
            return Response({"xAxis": [], "results_series": [], "predictions_series": []})
        try:
            periods_count = int(request.query_params.get("periods_count"))
        except TypeError:  # Handle None value of query_params.periods_count
            periods_count = None

        # Database query
        queryset_fields = ["name"]
        periods = BudgetingPeriod.objects.filter(budget_id=budget_pk).order_by("-date_start")
        get_results = partial(get_period_transfers_sum_in_category, category_id=category_id)
        get_predictions = partial(get_period_predictions_for_category, category_id=category_id)
        if display_value == str(DisplayValueChoices.RESULTS.value):
            periods = periods.annotate(results=get_results())
            queryset_fields.append("results")
        elif display_value == str(DisplayValueChoices.PREDICTIONS.value):
            periods = periods.annotate(predictions=get_predictions())
            queryset_fields.append("predictions")
        else:
            periods = periods.annotate(results=get_results(), predictions=get_predictions())
            queryset_fields.extend(["results", "predictions"])
        periods = periods.values(*queryset_fields)[:periods_count]

        # Response
        response = {"xAxis": [], "results_series": [], "predictions_series": []}
        for period in periods:
            response["xAxis"].insert(0, period["name"])
            if display_value == str(DisplayValueChoices.RESULTS.value):
                response["results_series"].insert(0, period["results"])
            elif display_value == str(DisplayValueChoices.PREDICTIONS.value):
                response["predictions_series"].insert(0, period["predictions"])
            else:
                response["results_series"].insert(0, period["results"])
                response["predictions_series"].insert(0, period["predictions"])
        return Response(response)
