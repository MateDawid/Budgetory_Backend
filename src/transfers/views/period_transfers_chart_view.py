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


def get_period_transfers_sum(transfer_type: CategoryType) -> Coalesce:
    """
    Calculates given Transfer type Transfers in Period.

    Args:
        transfer_type (CategoryType): Type of Transfer.

    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    return Coalesce(
        Subquery(
            Transfer.objects.filter(Q(period_id=OuterRef("id"), transfer_type=transfer_type))
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
        response = {"xAxis": [], "expense_series": [], "income_series": []}

        periods = (
            BudgetingPeriod.objects.filter(budget_id=budget_pk)
            .order_by("date_start")
            .annotate(
                expenses=get_period_transfers_sum(CategoryType.EXPENSE),
                incomes=get_period_transfers_sum(CategoryType.INCOME),
            )
            .values("name", "expenses", "incomes")[:5]
        )

        for period in periods:
            response["xAxis"].append(period["name"])
            response["expense_series"].append(period["expenses"])
            response["income_series"].append(period["incomes"])

        return Response(response)
