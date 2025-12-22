from functools import partial

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


def get_period_transfers_sum(
    transfer_type: CategoryType, deposit_id: str | None = None, entity_id: str | None = None
) -> Coalesce:
    """
    Calculates given Transfer type Transfers in Period.

    Args:
        transfer_type (CategoryType): Type of Transfer.
        deposit_id (str | None): Deposit ID or None.
        entity_id (str | None): Entity ID or None.
    Returns:
        Coalesce: Django ORM Coalesce function with Transfer subquery.
    """
    transfer_kwargs: dict = {"transfer_type": transfer_type}
    if deposit_id:
        transfer_kwargs["deposit_id"] = deposit_id
    if entity_id:
        transfer_kwargs["entity_id"] = entity_id
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


class TransfersInPeriodsChartApiView(APIView):
    """
    API view for retrieving data about Transfers in Periods for chart purposes.

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
        # Query params
        deposit_id = request.query_params.get("deposit", None)
        entity_id = request.query_params.get("entity", None)
        transfer_type = request.query_params.get("transfer_type", None)
        try:
            periods_count = int(request.query_params.get("periods_count"))
        except TypeError:  # Handle None value of query_params.periods_count
            periods_count = None

        # Database query
        queryset_fields = ["name"]
        periods = BudgetingPeriod.objects.filter(budget_id=budget_pk).order_by("-date_start")
        get_incomes_sum = partial(
            get_period_transfers_sum, transfer_type=CategoryType.INCOME, deposit_id=deposit_id, entity_id=entity_id
        )
        get_expenses_sum = partial(
            get_period_transfers_sum, transfer_type=CategoryType.EXPENSE, deposit_id=deposit_id, entity_id=entity_id
        )
        if transfer_type == str(CategoryType.INCOME.value):
            periods = periods.annotate(incomes=get_incomes_sum())
            queryset_fields.append("incomes")
        elif transfer_type == str(CategoryType.EXPENSE.value):
            periods = periods.annotate(expenses=get_expenses_sum())
            queryset_fields.append("expenses")
        else:
            periods = periods.annotate(incomes=get_incomes_sum(), expenses=get_expenses_sum())
            queryset_fields.extend(["incomes", "expenses"])
        periods = periods.values(*queryset_fields)[:periods_count]

        # Response
        response = {"xAxis": [], "expense_series": [], "income_series": []}
        for period in periods:
            response["xAxis"].insert(0, period["name"])
            if transfer_type == str(CategoryType.INCOME.value):
                response["income_series"].insert(0, period["incomes"])
            elif transfer_type == str(CategoryType.EXPENSE.value):
                response["expense_series"].insert(0, period["expenses"])
            else:
                response["income_series"].insert(0, period["incomes"])
                response["expense_series"].insert(0, period["expenses"])
        return Response(response)
