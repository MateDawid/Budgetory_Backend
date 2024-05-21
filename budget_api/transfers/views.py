from app_config.permissions import UserBelongsToBudgetPermission
from budgets.mixins import BudgetMixin
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from transfers.filters import ExpenseCategoryFilterSet, IncomeCategoryFilterSet
from transfers.models import TransferCategory
from transfers.serializers import (
    ExpenseCategorySerializer,
    IncomeCategorySerializer,
    TransferCategorySerializer,
)


class TransferCategoryViewSet(BudgetMixin, ModelViewSet):
    """Base view for managing TransferCategories."""

    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)

    def get_queryset(self) -> QuerySet:
        """
        Retrieve TransferCategories for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        budget = getattr(self.request, 'budget', None)
        return self.queryset.prefetch_related('owner').filter(budget=budget).distinct()

    def perform_create(self, serializer: TransferCategorySerializer) -> None:
        """
        Additionally save Budget from URL on TransferCategory instance during saving serializer.

        Args:
            serializer [TransferCategorySerializer]: Serializer for TransferCategory model.
        """
        serializer.save(budget=self.request.budget)


class ExpenseCategoryViewSet(TransferCategoryViewSet):
    serializer_class = ExpenseCategorySerializer
    queryset = TransferCategory.objects.expense_categories()
    filterset_class = ExpenseCategoryFilterSet
    ordering = ('id', 'expense_group', 'name')


class IncomeCategoryViewSet(TransferCategoryViewSet):
    serializer_class = IncomeCategorySerializer
    queryset = TransferCategory.objects.income_categories()
    filterset_class = IncomeCategoryFilterSet
    ordering = ('id', 'income_group', 'name')
