from datetime import date
from decimal import Decimal

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models.choices.category_type import CategoryType
from charts.views.category_results_and_predictions_in_periods_chart_view import DisplayValueChoices


def category_results_predictions_chart_url(budget_id: int) -> str:
    """Create and return a category results and predictions chart URL."""
    return reverse("charts:category-results-and-predictions-in-periods-chart", args=[budget_id])


@pytest.mark.django_db
class TestCategoryResultsAndPredictionsInPeriodsChartApiView:
    """Tests for CategoryResultsAndPredictionsInPeriodsChartApiView."""

    def test_auth_required(self, api_client: APIClient, budget_factory: FactoryMetaClass):
        """
        GIVEN: Budget instance in database.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        budget = budget_factory()

        response = api_client.get(category_results_predictions_chart_url(budget.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = category_results_predictions_chart_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance in database.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_chart_data_no_category_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called without category query parameter.
        THEN: HTTP 200 - Response with empty arrays returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["results_series"] == []
        assert response.data["predictions_series"] == []

    def test_get_chart_data_empty_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with no periods in database.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member with category.
        THEN: HTTP 200 - Response with empty xAxis, results_series, and predictions_series arrays returned.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)
        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["results_series"] == []
        assert response.data["predictions_series"] == []

    def test_get_chart_data_no_transfers_or_predictions(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods but no transfers or predictions in database.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with periods on xAxis and zero values in series.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)
        budgeting_period_factory(budget=budget, name="Jan 2024")
        budgeting_period_factory(budget=budget, name="Feb 2024")
        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["results_series"] == [Decimal("0"), Decimal("0")]
        assert response.data["predictions_series"] == [Decimal("0"), Decimal("0")]

    def test_get_chart_data_basic_scenario(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods, transfers, and predictions for a category.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct results and predictions calculations.
        """
        budget = budget_factory(members=[base_user])
        period1 = budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Period 1 data
        transfer_factory(period=period1, category=category, value=Decimal("500.00"), deposit=deposit)
        expense_prediction_factory(period=period1, category=category, current_plan=Decimal("600.00"))

        # Period 2 data
        transfer_factory(period=period2, category=category, value=Decimal("800.00"), deposit=deposit)
        expense_prediction_factory(period=period2, category=category, current_plan=Decimal("750.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["results_series"] == [Decimal("500.00"), Decimal("800.00")]
        assert response.data["predictions_series"] == [Decimal("600.00"), Decimal("750.00")]

    def test_get_chart_data_periods_ordered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods created in non-chronological order.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with periods ordered by date_start.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)

        # Create periods in non-chronological order
        budgeting_period_factory(
            budget=budget, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )
        budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]

    def test_get_chart_data_only_results(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with period containing only transfers (no predictions).
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with results and zero predictions.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("250.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results_series"] == [Decimal("250.00")]
        assert response.data["predictions_series"] == [Decimal("0")]

    def test_get_chart_data_only_predictions(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with period containing only predictions (no transfers).
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with predictions and zero results.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        expense_prediction_factory(period=period, category=category, current_plan=Decimal("750.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results_series"] == [Decimal("0")]
        assert response.data["predictions_series"] == [Decimal("750.00")]

    def test_get_chart_data_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers and predictions containing decimal values.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct decimal precision in calculations.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Multiple transfers with decimals
        transfer_factory(period=period, category=category, value=Decimal("123.45"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("67.89"), deposit=deposit)
        expense_prediction_factory(period=period, category=category, current_plan=Decimal("199.99"))

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results_series"] == [Decimal("191.34")]  # 123.45 + 67.89
        assert response.data["predictions_series"] == [Decimal("199.99")]

    def test_get_chart_data_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers and predictions containing large monetary values.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct calculations for large values.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("999999.99"), deposit=deposit)
        expense_prediction_factory(period=period, category=category, current_plan=Decimal("888888.88"))

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results_series"] == [Decimal("999999.99")]
        assert response.data["predictions_series"] == [Decimal("888888.88")]

    def test_display_value_results_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers and predictions for a category.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with display_value=DisplayValueChoices.RESULTS.
        THEN: HTTP 200 - Response with only results_series populated, predictions_series empty.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)
        expense_prediction_factory(period=period, category=category, current_plan=Decimal("600.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "display_value": DisplayValueChoices.RESULTS.value},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["results_series"] == [Decimal("500.00")]
        assert response.data["predictions_series"] == []

    def test_display_value_predictions_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers and predictions for a category.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called
        with display_value=DisplayValueChoices.PREDICTIONS.
        THEN: HTTP 200 - Response with only predictions_series populated, results_series empty.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)
        expense_prediction_factory(period=period, category=category, current_plan=Decimal("600.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "display_value": DisplayValueChoices.PREDICTIONS.value},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["results_series"] == []
        assert response.data["predictions_series"] == [Decimal("600.00")]

    def test_display_value_invalid_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers and predictions.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with invalid display_value.
        THEN: HTTP 200 - Response with both series populated (falls back to default behavior).
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)
        expense_prediction_factory(period=period, category=category, current_plan=Decimal("600.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id), {"category": str(category.id), "display_value": "999"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["results_series"] == [Decimal("500.00")]
        assert response.data["predictions_series"] == [Decimal("600.00")]

    def test_periods_count_parameter_custom_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with 8 periods.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with periods_count=3.
        THEN: HTTP 200 - Response with only last 3 periods.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)

        # Create 8 periods
        for month in range(1, 9):
            budgeting_period_factory(
                budget=budget,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "periods_count": 3},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["2024-06", "2024-07", "2024-08"]

    def test_periods_count_parameter_zero(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with periods_count=0.
        THEN: HTTP 200 - Response with empty arrays.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)
        budgeting_period_factory(budget=budget, name="Jan 2024")
        budgeting_period_factory(budget=budget, name="Feb 2024")

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "periods_count": 0},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["results_series"] == []
        assert response.data["predictions_series"] == []

    def test_periods_count_parameter_exceeds_available_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with 3 periods.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with periods_count=10.
        THEN: HTTP 200 - Response with all 3 available periods.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)
        budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )
        budgeting_period_factory(
            budget=budget, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "periods_count": 10},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]

    def test_periods_count_parameter_one(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple periods, transfers, and predictions.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with periods_count=1.
        THEN: HTTP 200 - Response with only the most recent period.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        period1 = budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        transfer_factory(period=period1, category=category, value=Decimal("100.00"), deposit=deposit)
        expense_prediction_factory(period=period1, category=category, current_plan=Decimal("150.00"))

        transfer_factory(period=period2, category=category, value=Decimal("200.00"), deposit=deposit)
        expense_prediction_factory(period=period2, category=category, current_plan=Decimal("250.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "periods_count": 1},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Feb 2024"]
        assert response.data["results_series"] == [Decimal("200.00")]
        assert response.data["predictions_series"] == [Decimal("250.00")]

    def test_combined_display_value_and_periods_count(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple periods, transfers, and predictions.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with both display_value and periods_count.
        THEN: HTTP 200 - Response with filtered data for specified display_value and number of periods.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Create 5 periods
        periods = []
        for month in range(1, 6):
            period = budgeting_period_factory(
                budget=budget,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            periods.append(period)

        # Add transfers and predictions for all periods
        for idx, period in enumerate(periods, start=1):
            transfer_factory(period=period, category=category, value=Decimal(f"{idx * 100}.00"), deposit=deposit)
            expense_prediction_factory(period=period, category=category, current_plan=Decimal(f"{idx * 150}.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id),
            {"category": str(category.id), "display_value": DisplayValueChoices.RESULTS.value, "periods_count": 3},
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["2024-03", "2024-04", "2024-05"]
        assert response.data["results_series"] == [Decimal("300.00"), Decimal("400.00"), Decimal("500.00")]
        assert response.data["predictions_series"] == []

    def test_multiple_transfers_same_category_same_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple transfers in same category in same period.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correctly summed transfer values.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Multiple transfers for same category
        transfer_factory(period=period, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("300.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("50.50"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["results_series"] == [Decimal("650.50")]
        assert response.data["predictions_series"] == [Decimal("0")]

    def test_nonexistent_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with transfers.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with nonexistent category ID.
        THEN: HTTP 200 - Response with zero values for all periods.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit)

        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        # Use an ID that doesn't exist
        from categories.models import TransferCategory

        nonexistent_id = TransferCategory.objects.filter(budget=budget).order_by("-id").first().id + 1

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(nonexistent_id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["results_series"] == [Decimal("0")]
        assert response.data["predictions_series"] == [Decimal("0")]

    def test_income_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with income category and transfers.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called for income category.
        THEN: HTTP 200 - Response with correct income data.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=income_category, value=Decimal("1500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(
            category_results_predictions_chart_url(budget.id), {"category": str(income_category.id)}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["results_series"] == [Decimal("1500.00")]
        assert response.data["predictions_series"] == [Decimal("0")]

    def test_mixed_periods_with_and_without_data(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple periods, some with data and some without.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct values, including zeros for periods without data.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        period1 = budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )
        period3 = budgeting_period_factory(
            budget=budget, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        # Period 1: has both results and predictions
        transfer_factory(period=period1, category=category, value=Decimal("100.00"), deposit=deposit)
        expense_prediction_factory(period=period1, category=category, current_plan=Decimal("150.00"))

        # Period 2: no data

        # Period 3: has only results
        transfer_factory(period=period3, category=category, value=Decimal("300.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": str(category.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]
        assert response.data["results_series"] == [Decimal("100.00"), Decimal("0"), Decimal("300.00")]
        assert response.data["predictions_series"] == [Decimal("150.00"), Decimal("0"), Decimal("0")]

    def test_category_empty_string(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods.
        WHEN: CategoryResultsAndPredictionsInPeriodsChartApiView called with empty string category parameter.
        THEN: HTTP 200 - Response with empty arrays (same as no category parameter).
        """
        budget = budget_factory(members=[base_user])
        budgeting_period_factory(budget=budget, name="Jan 2024")

        api_client.force_authenticate(base_user)

        response = api_client.get(category_results_predictions_chart_url(budget.id), {"category": ""})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["results_series"] == []
        assert response.data["predictions_series"] == []
