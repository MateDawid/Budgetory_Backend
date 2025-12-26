from django.urls import path

from charts.views.categories_in_periods_chart_view import CategoriesInPeriodsChartAPIView
from charts.views.category_results_and_predictions_in_periods_chart_view import (
    CategoryResultsAndPredictionsInPeriodsChartApiView,
)
from charts.views.deposits_in_periods_chart_view import DepositsInPeriodsChartAPIView
from charts.views.top_entities_in_period_chart_view import TopEntitiesInPeriodChartAPIView
from charts.views.transfers_in_periods_chart_view import TransfersInPeriodsChartApiView

app_name = "charts"

urlpatterns = [
    path(
        "budgets/<int:budget_pk>/charts/deposits_in_periods/",
        DepositsInPeriodsChartAPIView.as_view(),
        name="deposits-in-periods-chart",
    ),
    path(
        "budgets/<int:budget_pk>/charts/transfers_in_periods/",
        TransfersInPeriodsChartApiView.as_view(),
        name="transfers-in-periods-chart",
    ),
    path(
        "budgets/<int:budget_pk>/charts/categories_in_periods/",
        CategoriesInPeriodsChartAPIView.as_view(),
        name="categories-in-periods-chart",
    ),
    path(
        "budgets/<int:budget_pk>/charts/top_entities_in_period/",
        TopEntitiesInPeriodChartAPIView.as_view(),
        name="top-entities-in-period-chart",
    ),
    path(
        "budgets/<int:budget_pk>/charts/category_results_and_predictions_in_periods/",
        CategoryResultsAndPredictionsInPeriodsChartApiView.as_view(),
        name="category-results-and-predictions-in-periods-chart",
    ),
]
