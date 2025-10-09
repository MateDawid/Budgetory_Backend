from typing import Callable

from django.utils.functional import _StrPromise
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType


def format_typed_priorities(
    priorities: tuple[CategoryPriority, ...]
) -> list[tuple[Callable[[], int], Callable[[], str | _StrPromise]]]:
    """
    Function to prepare select choices of CategoryPriority filtered values on frontend.
    Args:
        priorities (tuple[CategoryPriority, ...]): List of filtered CategoryPriority choices.

    Returns:
        list[tuple[Callable[[], int], Callable[[], str | _StrPromise]]]: Formatted priorities.
    """
    return [(priority.value, priority.label) for priority in priorities]


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
        choices = []
        match int(request.query_params.get("type", 0)):
            case CategoryType.INCOME.value:
                choices = format_typed_priorities(CategoryPriority.income_priorities())
            case CategoryType.EXPENSE.value:
                choices = format_typed_priorities(CategoryPriority.expense_priorities())
            case _:
                choices = CategoryPriority.choices

        return Response({"results": [{"value": choice[0], "label": choice[1]} for choice in choices]})
