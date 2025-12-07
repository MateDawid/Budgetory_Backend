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


def period_transfers_chart_url(budget_id: int) -> str:
    """Create and return a period transfers chart URL."""
    return reverse("transfers:period-transfers-chart", args=[budget_id])


@pytest.mark.django_db
class TestPeriodTransfersChartApiView:
    """Tests for PeriodTransfersChartApiView."""

    def test_auth_required(self, api_client: APIClient, budget_factory: FactoryMetaClass):
        """
        GIVEN: Budget instance in database.
        WHEN: PeriodTransfersChartApiView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        budget = budget_factory()

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: PeriodTransfersChartApiView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = period_transfers_chart_url(budget.id)
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
        WHEN: PeriodTransfersChartApiView called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_chart_data_empty_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with no periods in database.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with empty xAxis, expense_series, and income_series arrays returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["expense_series"] == []
        assert response.data["income_series"] == []

    def test_get_chart_data_no_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods but no transfers in database.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with periods on xAxis and zero values in series.
        """
        budget = budget_factory(members=[base_user])
        budgeting_period_factory(budget=budget, name="Jan 2024")
        budgeting_period_factory(budget=budget, name="Feb 2024")
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["expense_series"] == [Decimal("0"), Decimal("0")]
        assert response.data["income_series"] == [Decimal("0"), Decimal("0")]

    def test_get_chart_data_basic_scenario(
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
        GIVEN: Budget with periods and transfers.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct expense and income calculations.
        """
        budget = budget_factory(members=[base_user])
        period1 = budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        deposit = deposit_factory(budget=budget, owner=base_user)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Period 1 transfers
        transfer_factory(period=period1, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period1, category=expense_category, value=Decimal("500.00"), deposit=deposit)

        # Period 2 transfers
        transfer_factory(period=period2, category=income_category, value=Decimal("1500.00"), deposit=deposit)
        transfer_factory(period=period2, category=expense_category, value=Decimal("800.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["expense_series"] == [Decimal("500.00"), Decimal("800.00")]
        assert response.data["income_series"] == [Decimal("1000.00"), Decimal("1500.00")]

    def test_get_chart_data_multiple_deposits(
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
        GIVEN: Budget with period and transfers from multiple deposits.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with aggregated expenses and incomes from all deposits.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")

        # Create two deposits with categories and transfers
        deposit1 = deposit_factory(budget=budget, owner=base_user)
        income_category1 = transfer_category_factory(budget=budget, deposit=deposit1, category_type=CategoryType.INCOME)
        expense_category1 = transfer_category_factory(
            budget=budget, deposit=deposit1, category_type=CategoryType.EXPENSE
        )

        deposit2 = deposit_factory(budget=budget, owner=base_user)
        income_category2 = transfer_category_factory(budget=budget, deposit=deposit2, category_type=CategoryType.INCOME)
        expense_category2 = transfer_category_factory(
            budget=budget, deposit=deposit2, category_type=CategoryType.EXPENSE
        )

        # Transfers for deposit1
        transfer_factory(period=period, category=income_category1, value=Decimal("300.00"), deposit=deposit1)
        transfer_factory(period=period, category=expense_category1, value=Decimal("100.00"), deposit=deposit1)

        # Transfers for deposit2
        transfer_factory(period=period, category=income_category2, value=Decimal("700.00"), deposit=deposit2)
        transfer_factory(period=period, category=expense_category2, value=Decimal("400.00"), deposit=deposit2)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("500.00")]  # 100 + 400
        assert response.data["income_series"] == [Decimal("1000.00")]  # 300 + 700

    def test_get_chart_data_limit_five_latest_periods(
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
        GIVEN: Budget with more than five periods.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with only last five periods (ordered by -date_start).
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget, owner=base_user)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Create 8 periods
        periods = []
        for month in range(1, 9):
            period = budgeting_period_factory(
                budget=budget,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            periods.append(period)
            # Add some transfers to each period
            transfer_factory(
                period=period, category=income_category, value=Decimal(f"{month * 100}.00"), deposit=deposit
            )
            transfer_factory(
                period=period, category=expense_category, value=Decimal(f"{month * 50}.00"), deposit=deposit
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 5
        assert response.data["xAxis"] == ["2024-04", "2024-05", "2024-06", "2024-07", "2024-08"]
        assert len(response.data["expense_series"]) == 5
        assert len(response.data["income_series"]) == 5
        # Verify correct values for first 5 periods
        assert response.data["income_series"] == [
            Decimal("400.00"),
            Decimal("500.00"),
            Decimal("600.00"),
            Decimal("700.00"),
            Decimal("800.00"),
        ]
        assert response.data["expense_series"] == [
            Decimal("200.00"),
            Decimal("250.00"),
            Decimal("300.00"),
            Decimal("350.00"),
            Decimal("400.00"),
        ]

    def test_get_chart_data_periods_ordered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods created in non-chronological order.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with periods ordered by date_start.
        """
        budget = budget_factory(members=[base_user])

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

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]

    def test_get_chart_data_only_expenses(
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
        GIVEN: Budget with period containing only expense transfers.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with expenses and zero incomes.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget, owner=base_user)
        expense_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=expense_category, value=Decimal("250.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["expense_series"] == [Decimal("250.00")]
        assert response.data["income_series"] == [Decimal("0")]

    def test_get_chart_data_only_incomes(
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
        GIVEN: Budget with period containing only income transfers.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with incomes and zero expenses.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget, owner=base_user)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=income_category, value=Decimal("750.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["expense_series"] == [Decimal("0")]
        assert response.data["income_series"] == [Decimal("750.00")]

    def test_get_chart_data_decimal_precision(
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
        GIVEN: Budget with transfers containing decimal values.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct decimal precision in calculations.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget, owner=base_user)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Multiple transfers with decimals
        transfer_factory(period=period, category=income_category, value=Decimal("123.45"), deposit=deposit)
        transfer_factory(period=period, category=income_category, value=Decimal("67.89"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("45.67"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("12.34"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_series"] == [Decimal("191.34")]  # 123.45 + 67.89
        assert response.data["expense_series"] == [Decimal("58.01")]  # 45.67 + 12.34

    def test_get_chart_data_large_values(
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
        GIVEN: Budget with transfers containing large monetary values.
        WHEN: PeriodTransfersChartApiView called by Budget member.
        THEN: HTTP 200 - Response with correct calculations for large values.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Jan 2024")
        deposit = deposit_factory(budget=budget, owner=base_user)
        income_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("999999.99"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("888888.88"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_series"] == [Decimal("999999.99")]
        assert response.data["expense_series"] == [Decimal("888888.88")]
