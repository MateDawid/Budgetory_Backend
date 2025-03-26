from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from budgets.models.choices.period_status import PeriodStatus


class PeriodStatusView(APIView):
    """
    View returning PeriodStatus choices for BudgetingPeriod.
    """

    choices = PeriodStatus.choices
    permission_classes = []

    def get(self, request: Request) -> Response:
        """
        Returns list of dictionaries containing possible choices for status field of BudgetingPeriod.

        Args:
            request [Request]: User request.

        Returns:
            Response: status field choices for BudgetingPeriod.
        """
        return Response({"results": [{"value": choice[0], "label": choice[1]} for choice in self.choices]})
