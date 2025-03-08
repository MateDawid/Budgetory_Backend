from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models.choices.category_priority import CategoryPriority


class CategoryPriorityView(APIView):
    """
    View returning CategoryPriority choices for TransferCategory.
    """

    choices = CategoryPriority.choices
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
