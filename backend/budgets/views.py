from app_config.permissions import UserBelongsToBudgetPermission
from budgets.mixins import BudgetMixin
from budgets.models import Budget, BudgetingPeriod
from budgets.serializers import BudgetingPeriodSerializer, BudgetSerializer
from django.db.models import Q, QuerySet
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class BudgetViewSet(viewsets.ModelViewSet):
    """View for manage Budgets."""

    serializer_class = BudgetSerializer
    queryset = Budget.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve Budgets for authenticated User."""
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return self.queryset.filter(Q(owner=user) | Q(members=user)).order_by('id').distinct()
        return self.queryset.none()  # pragma: no cover

    @action(detail=False, methods=['GET'])
    def owned(self, request, **kwargs):
        """Retrieves Budgets owned by authenticated User."""
        owned_budgets = self.queryset.filter(owner=self.request.user).order_by('id').distinct()
        serializer = self.get_serializer(owned_budgets, many=True)
        return Response({'results': serializer.data})

    @action(detail=False, methods=['GET'])
    def membered(self, request, **kwargs):
        """Retrieves Budgets in which authenticated User is a member."""
        membered_budgets = self.queryset.filter(members=self.request.user).order_by('id').distinct()
        serializer = self.get_serializer(membered_budgets, many=True)
        return Response({'results': serializer.data})

    def perform_create(self, serializer):
        """Save request User as owner of Budget model."""
        serializer.save(owner=self.request.user)


class BudgetingPeriodViewSet(BudgetMixin, viewsets.ModelViewSet):
    """View for manage BudgetingPeriods."""

    serializer_class = BudgetingPeriodSerializer
    queryset = BudgetingPeriod.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]

    def get_queryset(self) -> QuerySet:
        """
        Retrieves BudgetingPeriods for Budgets to which authenticated User belongs.

        Returns:
            QuerySet: Filtered BudgetingPeriod QuerySet.
        """
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            budget_pk = self.kwargs.get('budget_pk')
            if budget_pk:
                return (
                    self.queryset.filter(Q(budget__owner=user) | Q(budget__members=user), budget__pk=budget_pk)
                    .order_by('-date_start')
                    .distinct()
                )
        return self.queryset.none()  # pragma: no cover

    def perform_create(self, serializer: BudgetingPeriodSerializer) -> None:
        """
        Extended with saving Budget in BudgetingPeriod model.

        Args:
            serializer [BudgetingPeriodSerializer]: Serializer for BudgetingPeriod
        """
        serializer.save(budget=self.request.budget)
