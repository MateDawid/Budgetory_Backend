from django.urls import path

from charts.views.deposits_in_periods_chart_view import DepositsInPeriodsChartAPIView
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
]
