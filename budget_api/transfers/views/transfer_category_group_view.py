from app_config.permissions import UserBelongsToBudgetPermission
from budgets.mixins import BudgetMixin
from django.db.models import QuerySet
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from transfers.models.transfer_category_group_model import TransferCategoryGroup
from transfers.serializers.transfer_category_group_serializer import (
    TransferCategoryGroupSerializer,
)


class TransferCategoryGroupViewSet(BudgetMixin, viewsets.ModelViewSet):
    serializer_class = TransferCategoryGroupSerializer
    queryset = TransferCategoryGroup.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]

    def get_queryset(self) -> QuerySet:
        """
        Retrieve TransferCategoryGroups for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategoryGroup QuerySet.
        """
        return self.queryset.filter(budget=self.request.budget).distinct()

    def perform_create(self, serializer: TransferCategoryGroupSerializer) -> None:
        """
        Additionally save Budget from URL on TransferCategoryGroup instance during saving serializer.

        Args:
            serializer [TransferCategoryGroupSerializer]: Serializer for TransferCategoryGroup model.
        """
        serializer.save(budget=self.request.budget)
