from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from transfers.serializers.transfer_serializer import TransferSerializer


class TransferViewSet(ModelViewSet):
    """Base ViewSet for managing Transfers."""

    serializer_class = TransferSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "owner__name", "priority")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Transfer for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        return (
            self.serializer_class.Meta.model.objects.prefetch_related("period", "category")
            .filter(period__budget__pk=self.kwargs.get("budget_pk"))
            .distinct()
        )
