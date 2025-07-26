from decimal import Decimal

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import Budget
from categories.models.choices.category_priority import CategoryPriority


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
        budget_members = Budget.objects.get(pk=budget_pk).members.all().values("id", "username")
        for member in [{"id": None, "username": "Common"}, *budget_members]:
            user_data = {
                "user_id": member["id"],
                "user_username": member["username"],
                "period_id": period_pk,
                "predictions_sum": get_period_predictions_sum(user_id=member["id"], period_pk=period_pk),
                "period_balance": get_period_balance(user_id=member["id"], period_pk=period_pk),
                "period_expenses": get_period_expenses(user_id=member["id"], period_pk=period_pk),
            }
            response.append(user_data)
        return Response(response)


def get_period_predictions_sum(user_id: int, period_pk: int) -> Decimal:
    return Decimal("10.00")


def get_period_balance(user_id: int, period_pk: int) -> Decimal:
    return Decimal("10.00")


def get_period_expenses(user_id: int, period_pk: int) -> Decimal:
    return Decimal("10.00")
