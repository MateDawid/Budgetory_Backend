from django.db.models import DecimalField, Func, QuerySet, Sum
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from entities.filtersets.deposit_filterset import DepositFilterSet
from entities.models.deposit_model import Deposit
from entities.serializers.deposit_serializer import DepositSerializer


def calculate_deposit_balance() -> Func:
    """
    Function for calculate Transfers values sum for Deposit.

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values.
    """
    return Coalesce(Sum("deposit_transfers__value", output_field=DecimalField()), 0, output_field=DecimalField())


class DepositViewSet(ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]
    filterset_class = DepositFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "balance")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Deposits for Budget passed in URL and annotate them with sum of Transfers.

        Returns:
            QuerySet: Filtered Deposit QuerySet.
        """
        return (
            self.queryset.filter(budget__pk=self.kwargs.get("budget_pk"))
            .distinct()
            .annotate(balance=calculate_deposit_balance())
        )

    def perform_create(self, serializer: DepositSerializer) -> None:
        """
        Additionally save Budget from URL on Deposit instance during saving serializer. Create Entity object for
        Deposit representation in Transfers.

        Args:
            serializer [DepositSerializer]: Serializer for Deposit model.
        """
        serializer.save(budget_id=self.kwargs.get("budget_pk"), is_deposit=True)
