from app_config.permissions import UserBelongsToBudgetPermission
from budgets.mixins import BudgetMixin
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from transfers.filters import TransferCategoriesFilterSet
from transfers.models import TransferCategory
from transfers.serializers import TransferCategorySerializer


class TransferCategoryViewSet(BudgetMixin, viewsets.ModelViewSet):
    """View for managing TransferCategories."""

    serializer_class = TransferCategorySerializer
    queryset = TransferCategory.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = (IsAuthenticated, UserBelongsToBudgetPermission)
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    filterset_class = TransferCategoriesFilterSet
    ordering = ('id', 'group', 'name')

    def get_queryset(self) -> QuerySet:
        """
        Retrieve TransferCategories for Budget passed in URL.

        Returns:
            QuerySet: Filtered TransferCategory QuerySet.
        """
        budget = getattr(self.request, 'budget', None)
        return self.queryset.prefetch_related('owner', 'group').filter(group__budget=budget).distinct()
