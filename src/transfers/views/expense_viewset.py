from transfers.filtersets.expense_filterset import ExpenseFilterSet
from transfers.serializers.expense_serializer import ExpenseSerializer
from transfers.views.transfer_viewset import TransferViewSet


class ExpenseViewSet(TransferViewSet):
    """ViewSet for managing Expense."""

    serializer_class = ExpenseSerializer
    filterset_class = ExpenseFilterSet
