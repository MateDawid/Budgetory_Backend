from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from entities.filtersets.entity_filterset import EntityFilterSet
from entities.models.entity_model import Entity
from entities.serializers.entity_serializer import EntitySerializer


class EntityViewSet(ModelViewSet):
    """View for managing Entities."""

    serializer_class = EntitySerializer
    queryset = Entity.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]
    filterset_class = EntityFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "is_deposit")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Entities for Budget passed in URL.

        Returns:
            QuerySet: Filtered Entity QuerySet.
        """
        return self.queryset.filter(budget__pk=self.kwargs.get("budget_pk")).distinct()

    def perform_create(self, serializer: EntitySerializer) -> None:
        """
        Additionally save Budget from URL on Entity instance during saving serializer.

        Args:
            serializer [EntitySerializer]: Serializer for Entity model.
        """
        serializer.save(budget_id=self.kwargs.get("budget_pk"))
