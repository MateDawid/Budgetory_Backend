from django.db.models import DecimalField, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from categories.models.choices.category_type import CategoryType
from transfers.models import Transfer

DEFAULT_PERIODS_NUMBER_ON_CHART = 5


def get_period_transfers_sum(transfer_type: CategoryType, deposit_id: str | None = None) -> Coalesce:
    """
    Calculates given Transfer type Transfers in Period.

    Args:
        transfer_type (CategoryType): Type of Transfer.
        deposit_id (str | None): Deposit ID or None.

    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    transfer_kwargs: dict = {"transfer_type": transfer_type}
    if deposit_id:
        transfer_kwargs["deposit_id"] = deposit_id
    return Coalesce(
        Subquery(
            Transfer.objects.filter(Q(period_id=OuterRef("id"), **transfer_kwargs))
            .values("period")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class PeriodTransfersChartApiView(APIView):
    """
    API view for retrieving data about Transfers in last five Periods for chart purposes.

    Returns:
        Response containing:
            - xAxis: List of Period names for chart x-axis
            - expense_series: List of accumulated Expenses from all Deposits in Periods.
            - income_series: List of accumulated Incomes from all Deposits in Periods.
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
        deposit_id = request.query_params.get("deposit", None)
        try:
            periods_count = int(request.query_params.get("periods_count", DEFAULT_PERIODS_NUMBER_ON_CHART))
        except ValueError:
            periods_count = DEFAULT_PERIODS_NUMBER_ON_CHART

        response = {"xAxis": [], "expense_series": [], "income_series": []}

        periods = (
            BudgetingPeriod.objects.filter(budget_id=budget_pk)
            .order_by("-date_start")
            .annotate(
                expenses=get_period_transfers_sum(CategoryType.EXPENSE, deposit_id),
                incomes=get_period_transfers_sum(CategoryType.INCOME, deposit_id),
            )
            .values("name", "expenses", "incomes")[:periods_count]
        )

        for period in periods:
            response["xAxis"].insert(0, period["name"])
            response["expense_series"].insert(0, period["expenses"])
            response["income_series"].insert(0, period["incomes"])

        return Response(response)
