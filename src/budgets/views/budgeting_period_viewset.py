from decimal import Decimal

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
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from predictions.models import ExpensePrediction


def sum_period_transfers(transfer_type: CategoryType) -> Func:
    """
    Function for calculate Transfers values sum of given CategoryType for BudgetingPeriod.

    Args:
        transfer_type (CategoryType): Transfer type - INCOME or EXPENSE.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified CategoryType.
    """
    return Coalesce(
        Sum(
            "transfers__value",
            filter=Q(transfers__transfer_type=transfer_type),
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def prepare_predictions_on_period_activation(budget_pk: str, period_pk: str) -> None:
    """
    Function for updating ExpensePrediction data on Period activation.

    Args:
        budget_pk (str): Budget ID.
        period_pk (str): Period ID.
    """
    if not all((budget_pk, period_pk)):
        return
    # Set initial_value for predictions create by User
    ExpensePrediction.objects.filter(period__id=period_pk, initial_plan__isnull=True).update(
        initial_plan=F("current_plan")
    )
    # Create predictions with 0 value for not predicted categories
    predicted_categories_ids = ExpensePrediction.objects.filter(
        period__id=period_pk, period__budget__id=budget_pk
    ).values_list("category", flat=True)

    unpredicted_categories_ids = TransferCategory.objects.filter(
        ~Q(id__in=predicted_categories_ids),
        category_type=CategoryType.EXPENSE,
    ).values_list("id", flat=True)

    zero_predictions = [
        ExpensePrediction(
            period_id=period_pk,
            category_id=category_id,
            initial_plan=Decimal("0.00"),
            current_plan=Decimal("0.00"),
        )
        for category_id in unpredicted_categories_ids
    ]
    ExpensePrediction.objects.bulk_create(zero_predictions)


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
        Method extended with updating periods ExpensePredictions initial_plan field on activating
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
                prepare_predictions_on_period_activation(
                    budget_pk=kwargs.get("budget_pk", "0"), period_pk=kwargs.get("pk", "0")
                )
            return super().update(request, *args, **kwargs)
