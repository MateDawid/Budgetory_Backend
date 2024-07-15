from app_config.permissions import UserBelongsToBudgetPermission
from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from django.db import transaction
from django.db.models import QuerySet
from entities.models.entity import Entity
from entities.serializers import EntitySerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class EntityViewSet(ModelViewSet):
    """View for managing Entities."""

    serializer_class = EntitySerializer
    queryset = Entity.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Entities for Budget passed in URL.

        Returns:
            QuerySet: Filtered Entity QuerySet.
        """
        return self.queryset.filter(budget__pk=self.kwargs.get('budget_pk')).distinct()

    def perform_create(self, serializer: EntitySerializer) -> None:
        """
        Additionally save Budget from URL on Entity instance during saving serializer.

        Args:
            serializer [EntitySerializer]: Serializer for Entity model.
        """
        serializer.save(budget_id=self.kwargs.get('budget_pk'))


class DepositViewSet(ModelViewSet):
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
        return self.queryset.filter(budget__pk=self.kwargs.get('budget_pk')).distinct()

    def perform_create(self, serializer: DepositSerializer) -> None:
        """
        Additionally save Budget from URL on Deposit instance during saving serializer. Create Entity object for
        Deposit representation in Transfers.

        Args:
            serializer [DepositSerializer]: Serializer for Deposit model.
        """
        with transaction.atomic():
            deposit = serializer.save(budget_id=self.kwargs.get('budget_pk'))
            Entity.objects.create(
                budget=deposit.budget, name=deposit.name, description=deposit.description, deposit=deposit
            )
