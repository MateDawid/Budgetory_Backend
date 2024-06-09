from app_config.permissions import UserBelongsToBudgetPermission
from budgets.mixins import BudgetMixin
from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from django.db.models import QuerySet
from entities.models import Entity
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class DepositViewSet(BudgetMixin, viewsets.ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Deposits for Budget passed in URL.

        Returns:
            QuerySet: Filtered Deposit QuerySet.
        """
        budget = getattr(self.request, 'budget', None)
        return self.queryset.filter(budget=budget).distinct()

    def perform_create(self, serializer: DepositSerializer) -> None:
        """
        Additionally save Budget from URL on Deposit instance during saving serializer. Create Entity object for
        Deposit representation in Transfers.

        Args:
            serializer [DepositSerializer]: Serializer for Deposit model.
        """
        deposit = serializer.save(budget=self.request.budget)
        Entity.objects.create(
            budget=deposit.budget, name=deposit.name, description=deposit.description, deposit=deposit
        )
