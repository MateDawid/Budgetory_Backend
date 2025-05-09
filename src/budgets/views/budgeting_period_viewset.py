from django.db import transaction
from django.db.models import DecimalField, F, Func, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.filtersets.budgeting_period_filterset import BudgetingPeriodFilterSet
from budgets.models import BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from budgets.serializers.budgeting_period_serializer import BudgetingPeriodSerializer
from categories.models.choices.category_type import CategoryType
from predictions.models import ExpensePrediction


def sum_period_transfers(category_type: CategoryType) -> Func:
    """
    Function for calculate Transfers values sum of given CategoryType for BudgetingPeriod.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified CategoryType.
    """
    return Coalesce(
        Sum(
            "transfers__value",
            filter=Q(transfers__category__category_type=category_type),
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


class BudgetingPeriodViewSet(ModelViewSet):
    """View for manage BudgetingPeriods."""

    serializer_class = BudgetingPeriodSerializer
    queryset = BudgetingPeriod.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]
    filterset_class = BudgetingPeriodFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = (
        "id",
        "status",
        "name",
        "date_start",
        "date_end",
    )

    def get_queryset(self) -> QuerySet:
        """
        Retrieves BudgetingPeriods for Budgets to which authenticated User belongs.

        Returns:
            QuerySet: Filtered BudgetingPeriod QuerySet.
        """
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            budget_pk = self.kwargs.get("budget_pk")
            if budget_pk:
                return (
                    self.queryset.filter(budget__members=user, budget__pk=budget_pk)
                    .order_by("-date_start")
                    .distinct()
                    .annotate(
                        incomes_sum=sum_period_transfers(CategoryType.INCOME),
                        expenses_sum=sum_period_transfers(CategoryType.EXPENSE),
                    )
                )
        return self.queryset.none()  # pragma: no cover

    def perform_create(self, serializer: BudgetingPeriodSerializer) -> None:
        """
        Extended with saving Budget in BudgetingPeriod model.

        Args:
            serializer [BudgetingPeriodSerializer]: Serializer for BudgetingPeriod
        """
        serializer.save(budget_id=self.kwargs.get("budget_pk"))

    def update(self, request: Request, *args: list, **kwargs: dict) -> Response:
        """
        Method extended with updating periods ExpensePredictions initial_value field on activating
        BudgetingPeriod.

        Args:
            request (Request): User's request.
            *args (list): Additional arguments.
            **kwargs (dict): Keyword arguments.

        Returns:
            Response: Response object.
        """
        with transaction.atomic():
            if int(request.data.get("status", 0)) == PeriodStatus.ACTIVE.value:
                ExpensePrediction.objects.filter(period__id=kwargs.get("pk"), initial_value__isnull=True).update(
                    initial_value=F("current_value")
                )
            return super().update(request, *args, **kwargs)
