from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from categories.models.income_category_model import IncomeCategory
from categories.serializers.income_category_serializer import IncomeCategorySerializer


class IncomeCategoryViewSet(ModelViewSet):
    """Base view for managing TransferCategories."""

    serializer_class = IncomeCategorySerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering = ("id", "category_type", "priority")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve IncomeCategories for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        return (
            IncomeCategory.objects.prefetch_related("budget", "owner")
            .filter(budget__pk=self.kwargs.get("budget_pk"))
            .distinct()
        )

    def perform_create(self, serializer: IncomeCategorySerializer) -> None:
        """
        Additionally save Budget from URL on TransferCategory instance during saving serializer.

        Args:
            serializer [TransferCategorySerializer]: Serializer for TransferCategory model.
        """
        serializer.save(budget_id=self.kwargs.get("budget_pk"))
