from decimal import Decimal

from django.db import transaction
from django.db.models import F, QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.filtersets.transfer_category_filterset import TransferCategoryFilterSet
from categories.serializers.transfer_category_serializer import TransferCategorySerializer
from periods.models import Period
from periods.models.choices.period_status import PeriodStatus
from predictions.models import ExpensePrediction


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
        wallet_pk = self.kwargs.get("wallet_pk")
        with transaction.atomic():
            category = serializer.save(wallet_id=wallet_pk)
            ExpensePrediction.objects.bulk_create(
                ExpensePrediction(
                    deposit_id=category.deposit.pk,
                    category=category,
                    period_id=period_id,
                    initial_plan=Decimal("0.00"),
                    current_plan=Decimal("0.00"),
                )
                for period_id in Period.objects.filter(
                    wallet_id=wallet_pk, status__in=[PeriodStatus.ACTIVE, PeriodStatus.CLOSED]
                ).values_list("id", flat=True)
            )
