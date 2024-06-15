from app_config.permissions import UserBelongsToBudgetPermission
from app_config.viewsets import BudgetModelViewSet
from django.db.models import QuerySet
from entities.models import Entity
from entities.serializers import EntitySerializer
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class EntityViewSet(BudgetModelViewSet):
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
        return self.queryset.filter(budget=self.budget).distinct()

    def perform_create(self, serializer: EntitySerializer) -> None:
        """
        Additionally save Budget from URL on Entity instance during saving serializer.

        Args:
            serializer [EntitySerializer]: Serializer for Entity model.
        """
        serializer.save(budget=self.budget)
