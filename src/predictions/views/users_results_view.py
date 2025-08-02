from decimal import Decimal

from django.db.models import DecimalField, Func, OuterRef, Q, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import Budget
from categories.models.choices.category_priority import CategoryPriority
from transfers.models import Expense, Transfer

# def get_period_balance(period_ref: str) -> Func:
#     """
#     Function for calculate Transfers values sum of given TransferCategory in BudgetingPeriod.
#
#     Args:
#         period_ref (string): Period field name for OuterRef.
#
#     Returns:
#         Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified TransferCategory.
#     """
#
#     return Coalesce(
#         Subquery(
#             Transfer.objects.filter(period=OuterRef(period_ref))
#             .values("period")
#             .annotate(total=Sum("value"))
#             .values("total")[:1],
#             output_field=DecimalField(decimal_places=2),
#             ),
#         Value(0),
#         output_field=DecimalField(decimal_places=2),
#     )


def get_user_period_expenses(period_pk: int) -> Func:
    """
    Function for calculate Transfers values sum of given TransferCategory in BudgetingPeriod.

    Args:
        period_pk (string): Period field name for OuterRef.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified TransferCategory.
    """

    return Coalesce(
        Subquery(
            Expense.objects.filter(period=period_pk, category__owner__pk=OuterRef("pk"))
            .values("period")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class UsersResultsAPIView(APIView):
    """
    View returning CategoryPriority choices for TransferCategory.
    """

    choices = CategoryPriority.choices
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def get(self, request: Request, budget_pk: int, period_pk: int) -> Response:
        """
        Returns serialized UserResults in particular BudgetingPeriod.

        Args:
            request [Request]: User request.

        Returns:
            Response: Serialized UserResults in particular BudgetingPeriod.
        """
        response = []
        budget_members = (
            Budget.objects.get(pk=budget_pk)
            .members.all()
            .annotate(period_expenses=get_user_period_expenses(period_pk))
            .values("id", "username", "period_expenses")
        )
        # TODO - common user
        # {"id": None, "username": "🏦 Common"},

        for member in budget_members:
            user_data = {
                "user_id": member["id"],
                "user_username": member["username"],
                "period_id": period_pk,
                "predictions_sum": Decimal("10.00"),
                "period_balance": Decimal("10.00"),
                "period_expenses": member["period_expenses"],
            }
            response.append(user_data)
        return Response(response)
