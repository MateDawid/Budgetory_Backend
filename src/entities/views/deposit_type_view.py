from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from entities.models.choices.deposit_type import DepositType


class DepositTypeView(APIView):
    """
    View returning DepositType choices for Deposit.
    """

    choices = DepositType.choices
    permission_classes = []

    def get(self, request: Request) -> Response:
        """
        Returns list of dictionaries containing possible choices for deposit_type field of Deposit.

        Args:
            request [Request]: User request.

        Returns:
            Response: deposit_type field choices for Deposit.
        """
        return Response({"results": [{"value": choice[0], "label": choice[1]} for choice in self.choices]})
