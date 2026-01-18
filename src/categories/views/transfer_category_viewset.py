from django.db.models import F, QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.filtersets.transfer_category_filterset import TransferCategoryFilterSet
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


class TransferCategoryViewSet(ModelViewSet):
    """Base ViewSet for managing TransferCategories."""

    serializer_class = TransferCategorySerializer
    filterset_class = TransferCategoryFilterSet
    permission_classes = (IsAuthenticated, UserBelongsToWalletPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "category_type", "priority", "deposit")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve TransferCategories for Wallet passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        return (
            self.serializer_class.Meta.model.objects.prefetch_related("wallet", "deposit")
            .filter(wallet__pk=self.kwargs.get("wallet_pk"))
            .distinct()
            .annotate(deposit_display=F("deposit__name"))
        )

    def perform_create(self, serializer: TransferCategorySerializer) -> None:
        """
        Additionally save Wallet from URL on TransferCategory instance during saving serializer.

        Args:
            serializer [TransferCategorySerializer]: Serializer for TransferCategory model.
        """
        serializer.save(wallet_id=self.kwargs.get("wallet_pk"))
