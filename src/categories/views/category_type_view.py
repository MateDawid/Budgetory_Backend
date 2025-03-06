from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models.choices.category_type import CategoryType


class CategoryTypeView(APIView):
    """
    View returning CategoryType choices for TransferCategory.
    """

    choices = CategoryType.choices
    permission_classes = []

    def get(self, request: Request) -> Response:
        """
        Returns list of dictionaries containing possible choices for category_type field of TransferCategory.

        Args:
            request [Request]: User request.

        Returns:
            Response: category_type field choices for TransferCategory.
        """
        return Response({"results": [{"value": choice[0], "label": choice[1]} for choice in self.choices]})
