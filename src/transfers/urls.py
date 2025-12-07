from django.urls import path

from transfers.views.period_transfers_chart_view import PeriodTransfersChartApiView

app_name = "transfers"

urlpatterns = [
    path(
        "budgets/<int:budget_pk>/period_transfers_chart/",
        PeriodTransfersChartApiView.as_view(),
        name="period-transfers-chart",
    ),
]
