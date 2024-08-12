from app_infrastructure.permissions import UserBelongsToBudgetPermission
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from predictions.filters.expense_prediction_filterset import ExpensePredictionFilterSet
from predictions.models.expense_prediction_model import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import (
    ExpensePredictionSerializer,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class ExpensePredictionViewSet(ModelViewSet):
    """Base view for managing ExpensePredictions."""

    authentication_classes = [TokenAuthentication]
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    serializer_class = ExpensePredictionSerializer

    filterset_class = ExpensePredictionFilterSet
    ordering = ("period__name", "category__name")
    ordering_fields = ("id", "period", "category", "period__name", "category__name")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve ExpensePredictions for Budget passed in URL.

        Returns:
            QuerySet: Filtered ExpensePrediction QuerySet.
        """
        return ExpensePrediction.objects.filter(period__budget__pk=self.kwargs.get("budget_pk")).prefetch_related(
            "period", "category"
        )
