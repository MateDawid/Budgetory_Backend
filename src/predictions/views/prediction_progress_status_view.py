from enum import Enum

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class PredictionProgressStatus(Enum):
    NOT_USED = 1
    IN_PLANNED_RANGE = 2
    FULLY_UTILIZED = 3
    OVERUSED = 4

    def __str__(self):
        return {
            PredictionProgressStatus.NOT_USED: "⚪ Not used",
            PredictionProgressStatus.IN_PLANNED_RANGE: "🟡 In planned range",
            PredictionProgressStatus.FULLY_UTILIZED: "🟢 Fully utilized",
            PredictionProgressStatus.OVERUSED: "🔴 Overused",
        }[self]

    @classmethod
    def choices(cls):
        return [{"value": member.value, "label": str(member)} for member in cls]


class PredictionProgressStatusView(APIView):
    """
    View returning PredictionProgressStatus choices for ExpensePrediction.
    """

    permission_classes = []

    def get(self, request: Request) -> Response:
        """
        Returns list of dictionaries containing possible choices for progress_status filter
        for ExpensePrediction list view.

        Args:
            request [Request]: User request.

        Returns:
            Response: Progress status filter choices for ExpensePrediction list view.
        """
        return Response(PredictionProgressStatus.choices())
