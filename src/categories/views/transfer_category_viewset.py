from django.db.models import CharField, F, Func, QuerySet, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from categories.filtersets.transfer_category_filterset import TransferCategoryFilterSet
from categories.models.choices.category_priority import CategoryPriority
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


def get_category_owner_display() -> Func:
    """
    Function for generate display value of TransferCategory owner.

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values.
    """
    return Coalesce(
        F("owner__username"),
        Value("🏦 Common"),
        output_field=CharField(),
    )


class TransferCategoryViewSet(ModelViewSet):
    """Base ViewSet for managing TransferCategories."""

    serializer_class = TransferCategorySerializer
    filterset_class = TransferCategoryFilterSet
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "category_type", "priority", "owner")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve TransferCategories for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        return (
            self.serializer_class.Meta.model.objects.prefetch_related("budget", "owner")
            .filter(budget__pk=self.kwargs.get("budget_pk"))
            .exclude(priority__in=(CategoryPriority.DEPOSIT_INCOME, CategoryPriority.DEPOSIT_EXPENSE))
            .distinct()
            .annotate(owner_display=get_category_owner_display())
        )

    def perform_create(self, serializer: TransferCategorySerializer) -> None:
        """
        Additionally save Budget from URL on TransferCategory instance during saving serializer.

        Args:
            serializer [TransferCategorySerializer]: Serializer for TransferCategory model.
        """
        serializer.save(budget_id=self.kwargs.get("budget_pk"))
