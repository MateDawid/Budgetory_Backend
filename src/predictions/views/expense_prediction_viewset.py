from django.db.models import (
    Case,
    DecimalField,
    ExpressionWrapper,
    F,
    Func,
    OuterRef,
    QuerySet,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from predictions.filtersets.expense_prediction_filterset import ExpensePredictionFilterSet
from predictions.models.expense_prediction_model import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer
from transfers.models import Transfer


def sum_period_transfers_with_category(period_ref: str) -> Func:
    """
    Function for calculate Transfers values sum of given TransferCategory in BudgetingPeriod.

    Args:
        period_ref (string): Period field name for OuterRef.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified TransferCategory.
    """

    return Coalesce(
        Subquery(
            Transfer.objects.filter(period=OuterRef(period_ref), category=OuterRef("category"))
            .values("period", "category")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def get_previous_period_prediction_plan() -> Func:
    """
    Function for calculate Transfers values sum of given TransferCategory in particular BudgetingPeriod.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified TransferCategory.
    """
    return Coalesce(
        Subquery(
            ExpensePrediction.objects.filter(
                period=OuterRef("period__previous_period"), category=OuterRef("category")
            ).values("current_plan")[:1]
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def get_current_funds_left() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in particular BudgetingPeriod.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in particular BudgetingPeriod.
    """
    return ExpressionWrapper(F("current_plan") - F("current_result"), output_field=DecimalField(decimal_places=2))


def get_current_progress() -> Case:
    """
    Function for calculate current percentage progress of given TransferCategory in particular BudgetingPeriod.

    Returns:
        Case: ORM function returning percentage progress of specified
        TransferCategory in particular BudgetingPeriod.
    """
    return Case(
        When(current_plan=0, then=Value(0)),
        default=ExpressionWrapper(
            F("current_result") / F("current_plan") * 100, output_field=DecimalField(decimal_places=2)
        ),
        output_field=DecimalField(decimal_places=2),
    )


def get_previous_funds_left() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in previous BudgetingPeriod.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in previous BudgetingPeriod.
    """
    return ExpressionWrapper(F("previous_plan") - F("previous_result"), output_field=DecimalField(decimal_places=2))


class ExpensePredictionViewSet(ModelViewSet):
    """Base view for managing ExpensePredictions."""

    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    serializer_class = ExpensePredictionSerializer

    filterset_class = ExpensePredictionFilterSet
    ordering_fields = (
        "id",
        "category__name",
        "category__priority",
        "current_plan",
        "current_result",
        "current_funds_left",
        "current_progress",
        "previous_result",
        "previous_funds_left",
    )

    def get_queryset(self) -> QuerySet:
        """
        Retrieve ExpensePredictions for Budget passed in URL.

        Returns:
            QuerySet: Filtered ExpensePrediction QuerySet.
        """
        return (
            ExpensePrediction.objects.filter(period__budget__pk=self.kwargs.get("budget_pk"))
            .select_related(
                "period",
                "period__budget",
                "period__previous_period",
                "category",
                "category__budget",
                "category__deposit",
            )
            .annotate(
                current_result=sum_period_transfers_with_category(period_ref="period"),
                previous_plan=get_previous_period_prediction_plan(),
                previous_result=sum_period_transfers_with_category(period_ref="period__previous_period"),
            )
            .annotate(
                current_funds_left=get_current_funds_left(),
                current_progress=get_current_progress(),
                previous_funds_left=get_previous_funds_left(),
            )
            .order_by("id")
        )
