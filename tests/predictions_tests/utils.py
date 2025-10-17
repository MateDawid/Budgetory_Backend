from django.db.models import QuerySet

from predictions.views.expense_prediction_viewset import (
    get_current_funds_left,
    get_current_progress,
    get_previous_funds_left,
    get_previous_period_prediction_plan,
    sum_period_transfers_with_category,
)


def annotate_expense_prediction_queryset(queryset: QuerySet) -> QuerySet:
    """
    Annotates QuerySet with calculated fields returned in ExpensePredictionViewSet.

    Args:
        queryset (QuerySet): Input ExpensePrediction QuerySet

    Returns:
        QuerySet: Annotated ExpensePrediction QuerySet.
    """
    return queryset.annotate(
        current_result=sum_period_transfers_with_category(period_ref="period"),
        previous_plan=get_previous_period_prediction_plan(),
        previous_result=sum_period_transfers_with_category(period_ref="period__previous_period"),
    ).annotate(
        current_funds_left=get_current_funds_left(),
        current_progress=get_current_progress(),
        previous_funds_left=get_previous_funds_left(),
    )
