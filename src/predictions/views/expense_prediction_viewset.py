from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from predictions.filtersets.expense_prediction_filterset import ExpensePredictionFilterSet
from predictions.models.expense_prediction_model import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer


class ExpensePredictionViewSet(ModelViewSet):
    """Base view for managing ExpensePredictions."""

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    serializer_class = ExpensePredictionSerializer

    filterset_class = ExpensePredictionFilterSet
    ordering_fields = ("id", "period", "category", "initial_value", "current_value")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve ExpensePredictions for Budget passed in URL.

        Returns:
            QuerySet: Filtered ExpensePrediction QuerySet.
        """
        return ExpensePrediction.objects.filter(period__budget__pk=self.kwargs.get("budget_pk")).prefetch_related(
            "period", "category"
        )
