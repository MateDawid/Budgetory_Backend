from django.db import models
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class TransferCategoryPriorityView(APIView):
    """
    View returning IncomeCategoryPriority choices for IncomeCategory.
    """

    choices = models.IntegerChoices.choices
    permission_classes = []

    def get(self, request: Request) -> Response:
        """
        Returns list of dictionaries containing possible choices for priority field of TransferCategory.

        Args:
            request [Request]: User request.

        Returns:
            Response: Priority field choices for TransferCategory.
        """
        return Response({"results": [{"value": choice[0], "label": choice[1]} for choice in self.choices]})
