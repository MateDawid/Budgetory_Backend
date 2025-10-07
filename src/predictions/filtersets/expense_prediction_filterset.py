from decimal import Decimal

from django.db.models import F, QuerySet
from django_filters import rest_framework as filters

from budgets.models import BudgetingPeriod
from budgets.utils import get_budget_pk
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from predictions.views.prediction_progress_status_view import PredictionProgressStatus


class ExpensePredictionFilterSet(filters.FilterSet):
    """FilterSet for ExpensePrediction endpoints."""

    period = filters.ModelChoiceFilter(
        queryset=lambda request: BudgetingPeriod.objects.filter(budget__pk=get_budget_pk(request))
    )
    category = filters.ModelChoiceFilter(
        queryset=lambda request: TransferCategory.objects.filter(
            budget__pk=get_budget_pk(request), category_type=CategoryType.EXPENSE
        )
    )
    owner = filters.NumberFilter(method="get_owner")
    initial_plan = filters.NumberFilter()
    initial_plan_min = filters.NumberFilter(field_name="initial_plan", lookup_expr="gte")
    initial_plan_max = filters.NumberFilter(field_name="initial_plan", lookup_expr="lte")
    current_plan = filters.NumberFilter()
    current_plan_min = filters.NumberFilter(field_name="current_plan", lookup_expr="gte")
    current_plan_max = filters.NumberFilter(field_name="current_plan", lookup_expr="lte")
    progress_status = filters.NumberFilter(method="get_progress_status")

    @staticmethod
    def get_owner(queryset: QuerySet, name: str, value: Decimal) -> QuerySet:
        """
        Filters ExpensePredictions queryset by Transfer Category owner field value.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [Decimal]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        if value == Decimal("-1"):
            return queryset.filter(category__owner__isnull=True)
        return queryset.filter(category__owner__id=value)

    @staticmethod
    def get_progress_status(queryset: QuerySet, name: str, value: Decimal) -> QuerySet:
        """
        Filters ExpensePredictions queryset by Transfer Category progress_status field value.

        Args:
            queryset [QuerySet]: Input QuerySet
            name [str]: Name of filtered param
            value [Decimal]: Value of filtered param

        Returns:
            QuerySet: Filtered QuerySet.
        """
        match int(value):
            case PredictionProgressStatus.NOT_USED.value:
                return queryset.filter(current_funds_left=F("current_plan"))
            case PredictionProgressStatus.IN_PLANNED_RANGE.value:
                return queryset.filter(current_funds_left__gt=0, current_funds_left__lt=F("current_plan"))
            case PredictionProgressStatus.FULLY_UTILIZED.value:
                return queryset.filter(current_funds_left=0)
            case PredictionProgressStatus.OVERUSED.value:
                return queryset.filter(current_funds_left__lt=0)
            case _:
                return queryset
