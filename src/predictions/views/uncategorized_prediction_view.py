from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Func, IntegerField, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from entities.models import Deposit
from predictions.serializers.uncategorized_expense_prediction_serializer import UncategorizedExpensePredictionSerializer
from transfers.models import Expense


def get_uncategorized_expenses_sum(period_id: int | OuterRef) -> Func:
    """
    Sums uncategorized Deposit Expenses in given Period.

    Args:
        period_id (int | OuterRef): Period id or OuterRef for Period field.

    Returns:
        Func: ORM function returning Sum of uncategorized Deposit Expenses values for specified Period.
    """
    return Coalesce(
        Subquery(
            Expense.objects.filter(period_id=period_id, deposit=OuterRef("id"), category=None)
            .values("period", "category")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class UncategorizedPredictionView(APIView):
    """
    View scanning Deposits for uncategorized Expenses and returning them as ExpensePrediction-like objects.
    """

    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)

    def get(self, request: Request, budget_pk: int, period_pk: int) -> Response:
        """
        Scans Deposits for uncategorized Expenses and returns them as ExpensePrediction-like objects.

        Args:
            request (Request): User Request.
            budget_pk (int): Budget id.
            period_pk (int): Period id.

        Returns:
            Response: Response containing serialized ExpensePrediction-like objects.
        """
        deposit_filters = {
            "budget_id": budget_pk,
        }
        if deposit_id := request.query_params.get("deposit"):
            deposit_filters["id"] = deposit_id

        uncategorized_predictions = (
            Deposit.objects.filter(**deposit_filters)
            .annotate(
                category_deposit=F("name"),
                period_id=Value(period_pk, output_field=IntegerField()),
                previous_period_id=Subquery(
                    BudgetingPeriod.objects.filter(pk=period_pk).values("previous_period__pk")[:1]
                ),
                current_result=get_uncategorized_expenses_sum(period_pk),
            )
            .annotate(
                previous_result=get_uncategorized_expenses_sum(OuterRef("previous_period_id")),
            )
            .annotate(
                current_funds_left=ExpressionWrapper(
                    Value(0) - F("current_result"), output_field=DecimalField(decimal_places=2)
                ),
                previous_funds_left=ExpressionWrapper(
                    Value(0) - F("previous_result"), output_field=DecimalField(decimal_places=2)
                ),
                current_progress=Value(0),
            )
            .filter(current_result__gt=Decimal("0.00"))
            .values(
                "category_deposit",
                "period_id",
                "current_result",
                "previous_result",
                "current_funds_left",
                "previous_funds_left",
                "current_progress",
            )
        )
        return Response(UncategorizedExpensePredictionSerializer(uncategorized_predictions, many=True).data)
