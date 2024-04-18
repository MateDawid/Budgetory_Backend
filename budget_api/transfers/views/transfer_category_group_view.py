from app_config.permissions import UserBelongToBudgetPermission
from budgets.mixins import BudgetMixin
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
    permission_classes = [IsAuthenticated, UserBelongToBudgetPermission]

    def perform_create(self, serializer: TransferCategoryGroupSerializer) -> None:
        """
        Additionally save Budget from URL on TransferCategoryGroup instance during saving serializer.

        Args:
            serializer [TransferCategoryGroupSerializer]: Serializer for TransferCategoryGroup model.
        """
        serializer.save(budget=self.request.budget)
