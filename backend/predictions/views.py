from app_config.permissions import UserBelongsToBudgetPermission
from django.db.models import QuerySet
from predictions.models import ExpensePrediction
from predictions.serializers import ExpensePredictionSerializer
from rest_framework import mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet


# class ExpensePredictionViewSet(ModelViewSet):
class ExpensePredictionViewSet(mixins.RetrieveModelMixin, mixins.ListModelMixin, GenericViewSet):
    """Base view for managing ExpensePredictions."""

    authentication_classes = [TokenAuthentication]
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    # filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    serializer_class = ExpensePredictionSerializer

    # filterset_class = ExpensePredictionFilterSet
    ordering = ('id', 'period', 'category')

    def get_queryset(self) -> QuerySet:
        """
        Retrieve ExpensePredictions for Budget passed in URL.

        Returns:
            QuerySet: Filtered ExpensePrediction QuerySet.
        """
        return ExpensePrediction.objects.filter(period__budget__pk=self.kwargs.get('budget_pk')).prefetch_related(
            'period', 'category'
        )
