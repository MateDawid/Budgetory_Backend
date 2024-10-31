from transfers.filtersets.income_filterset import IncomeFilterSet
from transfers.serializers.income_serializer import IncomeSerializer
from transfers.views.transfer_viewset import TransferViewSet


class IncomeViewSet(TransferViewSet):
    """ViewSet for managing Incomes."""

    serializer_class = IncomeSerializer
    filterset_class = IncomeFilterSet
