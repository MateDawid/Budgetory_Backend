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
from entities.models import Deposit


def period_transfers_chart_url(wallet_id: int) -> str:
    """Create and return a period transfers chart URL."""
    return reverse("charts:transfers-in-periods-chart", args=[wallet_id])


@pytest.mark.django_db
class TestTransfersInPeriodsChartApiView:
    """Tests for TransfersInPeriodsChartApiView."""

    def test_auth_required(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet instance in database.
        WHEN: TransfersInPeriodsChartApiView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransfersInPeriodsChartApiView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = period_transfers_chart_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance in database.
        WHEN: TransfersInPeriodsChartApiView called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_chart_data_empty_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with no periods in database.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis, expense_series, and income_series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["expense_series"] == []
        assert response.data["income_series"] == []

    def test_get_chart_data_no_transfers(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods but no transfers in database.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with periods on xAxis and zero values in series.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet, name="Jan 2024")
        period_factory(wallet=wallet, name="Feb 2024")
        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["expense_series"] == [Decimal("0"), Decimal("0")]
        assert response.data["income_series"] == [Decimal("0"), Decimal("0")]

    def test_get_chart_data_basic_scenario(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods and transfers.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with correct expense and income calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(
            wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = period_factory(
            wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Period 1 transfers
        transfer_factory(period=period1, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period1, category=expense_category, value=Decimal("500.00"), deposit=deposit)

        # Period 2 transfers
        transfer_factory(period=period2, category=income_category, value=Decimal("1500.00"), deposit=deposit)
        transfer_factory(period=period2, category=expense_category, value=Decimal("800.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["expense_series"] == [Decimal("500.00"), Decimal("800.00")]
        assert response.data["income_series"] == [Decimal("1000.00"), Decimal("1500.00")]

    def test_get_chart_data_multiple_deposits(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period and transfers from multiple deposits.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with aggregated expenses and incomes from all deposits.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        # Create two deposits with categories and transfers
        deposit1 = deposit_factory(wallet=wallet)
        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        expense_category1 = transfer_category_factory(
            wallet=wallet, deposit=deposit1, category_type=CategoryType.EXPENSE
        )

        deposit2 = deposit_factory(wallet=wallet)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)
        expense_category2 = transfer_category_factory(
            wallet=wallet, deposit=deposit2, category_type=CategoryType.EXPENSE
        )

        # Transfers for deposit1
        transfer_factory(period=period, category=income_category1, value=Decimal("300.00"), deposit=deposit1)
        transfer_factory(period=period, category=expense_category1, value=Decimal("100.00"), deposit=deposit1)

        # Transfers for deposit2
        transfer_factory(period=period, category=income_category2, value=Decimal("700.00"), deposit=deposit2)
        transfer_factory(period=period, category=expense_category2, value=Decimal("400.00"), deposit=deposit2)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("500.00")]  # 100 + 400
        assert response.data["income_series"] == [Decimal("1000.00")]  # 300 + 700

    def test_get_chart_data_periods_ordered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods created in non-chronological order.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with periods ordered by date_start.
        """
        wallet = wallet_factory(members=[base_user])

        # Create periods in non-chronological order
        period_factory(wallet=wallet, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31))
        period_factory(wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_factory(wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29))

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]

    def test_get_chart_data_only_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period containing only expense transfers.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with expenses and zero incomes.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=expense_category, value=Decimal("250.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["expense_series"] == [Decimal("250.00")]
        assert response.data["income_series"] == [Decimal("0")]

    def test_get_chart_data_only_incomes(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with period containing only income transfers.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with incomes and zero expenses.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=income_category, value=Decimal("750.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["expense_series"] == [Decimal("0")]
        assert response.data["income_series"] == [Decimal("750.00")]

    def test_get_chart_data_decimal_precision(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers containing decimal values.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with correct decimal precision in calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Multiple transfers with decimals
        transfer_factory(period=period, category=income_category, value=Decimal("123.45"), deposit=deposit)
        transfer_factory(period=period, category=income_category, value=Decimal("67.89"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("45.67"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("12.34"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_series"] == [Decimal("191.34")]  # 123.45 + 67.89
        assert response.data["expense_series"] == [Decimal("58.01")]  # 45.67 + 12.34

    def test_get_chart_data_large_values(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers containing large monetary values.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with correct calculations for large values.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("999999.99"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("888888.88"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_series"] == [Decimal("999999.99")]
        assert response.data["expense_series"] == [Decimal("888888.88")]

    def test_deposit_filter_single_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple deposits and transfers in period.
        WHEN: TransfersInPeriodsChartApiView called with deposit query parameter.
        THEN: HTTP 200 - Response with data only from specified deposit.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        # Create two deposits with categories and transfers
        deposit1 = deposit_factory(wallet=wallet)
        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        expense_category1 = transfer_category_factory(
            wallet=wallet, deposit=deposit1, category_type=CategoryType.EXPENSE
        )

        deposit2 = deposit_factory(wallet=wallet)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)
        expense_category2 = transfer_category_factory(
            wallet=wallet, deposit=deposit2, category_type=CategoryType.EXPENSE
        )

        # Transfers for deposit1
        transfer_factory(period=period, category=income_category1, value=Decimal("300.00"), deposit=deposit1)
        transfer_factory(period=period, category=expense_category1, value=Decimal("100.00"), deposit=deposit1)

        # Transfers for deposit2
        transfer_factory(period=period, category=income_category2, value=Decimal("700.00"), deposit=deposit2)
        transfer_factory(period=period, category=expense_category2, value=Decimal("400.00"), deposit=deposit2)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"deposit": str(deposit1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("100.00")]
        assert response.data["income_series"] == [Decimal("300.00")]

    def test_deposit_filter_nonexistent_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers in period.
        WHEN: TransfersInPeriodsChartApiView called with nonexistent deposit ID.
        THEN: HTTP 200 - Response with zero values for all periods.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=income_category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id),
            {"deposit": Deposit.objects.filter(wallet=wallet).order_by("-id").first().id + 1},
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("0")]
        assert response.data["income_series"] == [Decimal("0")]

    def test_deposit_filter_with_multiple_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple periods and deposits.
        WHEN: TransfersInPeriodsChartApiView called with deposit filter.
        THEN: HTTP 200 - Response with filtered data across all periods.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(
            wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = period_factory(
            wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)

        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)

        # Period 1: both deposits have transfers
        transfer_factory(period=period1, category=income_category1, value=Decimal("200.00"), deposit=deposit1)
        transfer_factory(period=period1, category=income_category2, value=Decimal("800.00"), deposit=deposit2)

        # Period 2: both deposits have transfers
        transfer_factory(period=period2, category=income_category1, value=Decimal("300.00"), deposit=deposit1)
        transfer_factory(period=period2, category=income_category2, value=Decimal("900.00"), deposit=deposit2)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"deposit": str(deposit1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert response.data["income_series"] == [Decimal("200.00"), Decimal("300.00")]
        assert response.data["expense_series"] == [Decimal("0"), Decimal("0")]

    def test_periods_count_parameter_custom_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with 8 periods.
        WHEN: TransfersInPeriodsChartApiView called with periods_count=3.
        THEN: HTTP 200 - Response with only last 3 periods.
        """
        wallet = wallet_factory(members=[base_user])

        # Create 8 periods
        for month in range(1, 9):
            period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"periods_count": 3})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["2024-06", "2024-07", "2024-08"]

    def test_periods_count_parameter_zero(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods.
        WHEN: TransfersInPeriodsChartApiView called with periods_count=0.
        THEN: HTTP 200 - Response with empty arrays.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet, name="Jan 2024")
        period_factory(wallet=wallet, name="Feb 2024")

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"periods_count": 0})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["expense_series"] == []
        assert response.data["income_series"] == []

    def test_periods_count_parameter_exceeds_available_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with 3 periods.
        WHEN: TransfersInPeriodsChartApiView called with periods_count=10.
        THEN: HTTP 200 - Response with all 3 available periods.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_factory(wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29))
        period_factory(wallet=wallet, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31))

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"periods_count": 10})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]

    def test_periods_count_parameter_one(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple periods and transfers.
        WHEN: TransfersInPeriodsChartApiView called with periods_count=1.
        THEN: HTTP 200 - Response with only the most recent period.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(
            wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = period_factory(
            wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period1, category=income_category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period2, category=income_category, value=Decimal("200.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"periods_count": 1})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Feb 2024"]
        assert response.data["income_series"] == [Decimal("200.00")]
        assert response.data["expense_series"] == [Decimal("0")]

    def test_combined_deposit_and_periods_count_filters(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple periods and deposits.
        WHEN: TransfersInPeriodsChartApiView called with both deposit and periods_count parameters.
        THEN: HTTP 200 - Response with filtered deposit data for specified number of periods.
        """
        wallet = wallet_factory(members=[base_user])

        # Create 5 periods
        periods = []
        for month in range(1, 6):
            period = period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            periods.append(period)

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)

        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)

        # Add transfers for both deposits in all periods
        for idx, period in enumerate(periods, start=1):
            transfer_factory(
                period=period, category=income_category1, value=Decimal(f"{idx * 100}.00"), deposit=deposit1
            )
            transfer_factory(
                period=period, category=income_category2, value=Decimal(f"{idx * 50}.00"), deposit=deposit2
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id), {"deposit": str(deposit1.id), "periods_count": 3}
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 3
        assert response.data["xAxis"] == ["2024-03", "2024-04", "2024-05"]
        assert response.data["income_series"] == [Decimal("300.00"), Decimal("400.00"), Decimal("500.00")]
        assert response.data["expense_series"] == [Decimal("0"), Decimal("0"), Decimal("0")]

    def test_deposit_filter_empty_string(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposits and transfers.
        WHEN: TransfersInPeriodsChartApiView called with empty string deposit parameter.
        THEN: HTTP 200 - Response should handle empty deposit filter appropriately.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=income_category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"deposit": ""})

        assert response.status_code == status.HTTP_200_OK
        # Should likely treat empty string as no filter and return all deposits
        assert response.data["xAxis"] == ["Jan 2024"]

    def test_transfer_type_filter_income_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with both income and expense transfers.
        WHEN: TransfersInPeriodsChartApiView called with transfer_type=INCOME filter.
        THEN: HTTP 200 - Response with only income_series populated, expense_series empty.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id), {"transfer_type": str(CategoryType.INCOME.value)}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["income_series"] == [Decimal("1000.00")]
        assert response.data["expense_series"] == []

    def test_transfer_type_filter_expense_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with both income and expense transfers.
        WHEN: TransfersInPeriodsChartApiView called with transfer_type=EXPENSE filter.
        THEN: HTTP 200 - Response with only expense_series populated, income_series empty.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id), {"transfer_type": str(CategoryType.EXPENSE.value)}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("500.00")]
        assert response.data["income_series"] == []

    def test_transfer_type_filter_invalid_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers.
        WHEN: TransfersInPeriodsChartApiView called with invalid transfer_type value.
        THEN: HTTP 200 - Response with both series populated (falls back to default behavior).
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("500.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"transfer_type": "INVALID"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["income_series"] == [Decimal("1000.00")]
        assert response.data["expense_series"] == [Decimal("500.00")]

    def test_entity_filter_single_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple entities and transfers.
        WHEN: TransfersInPeriodsChartApiView called with entity query parameter.
        THEN: HTTP 200 - Response with data only from specified entity.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)

        entity1 = entity_factory(wallet=wallet)
        entity2 = entity_factory(wallet=wallet)

        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Transfers for entity1
        transfer_factory(
            period=period, category=income_category, value=Decimal("300.00"), deposit=deposit, entity=entity1
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("100.00"), deposit=deposit, entity=entity1
        )

        # Transfers for entity2
        transfer_factory(
            period=period, category=income_category, value=Decimal("700.00"), deposit=deposit, entity=entity2
        )
        transfer_factory(
            period=period, category=expense_category, value=Decimal("400.00"), deposit=deposit, entity=entity2
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id), {"entity": str(entity1.id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("100.00")]
        assert response.data["income_series"] == [Decimal("300.00")]

    def test_combined_deposit_entity_filters(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple deposits, entities, and transfers.
        WHEN: TransfersInPeriodsChartApiView called with both deposit and entity parameters.
        THEN: HTTP 200 - Response with data filtered by both deposit and entity.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)

        entity1 = entity_factory(wallet=wallet)
        entity2 = entity_factory(wallet=wallet)

        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)

        # Various combinations
        transfer_factory(
            period=period, category=income_category1, value=Decimal("100.00"), deposit=deposit1, entity=entity1
        )
        transfer_factory(
            period=period, category=income_category1, value=Decimal("200.00"), deposit=deposit1, entity=entity2
        )
        transfer_factory(
            period=period, category=income_category2, value=Decimal("300.00"), deposit=deposit2, entity=entity1
        )
        transfer_factory(
            period=period, category=income_category2, value=Decimal("400.00"), deposit=deposit2, entity=entity2
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id), {"deposit": str(deposit1.id), "entity": str(entity1.id)}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["income_series"] == [Decimal("100.00")]
        assert response.data["expense_series"] == [Decimal("0")]

    def test_combined_all_filters(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple periods, deposits, entities, and transfers.
        WHEN: TransfersInPeriodsChartApiView called with deposit, entity, transfer_type, and periods_count.
        THEN: HTTP 200 - Response with data filtered by all parameters.
        """
        wallet = wallet_factory(members=[base_user])

        periods = []
        for month in range(1, 4):
            period = period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            periods.append(period)

        deposit1 = deposit_factory(wallet=wallet)
        deposit2 = deposit_factory(wallet=wallet)
        entity1 = entity_factory(wallet=wallet)
        entity2 = entity_factory(wallet=wallet)

        income_category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        income_category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)
        expense_category1 = transfer_category_factory(
            wallet=wallet, deposit=deposit1, category_type=CategoryType.EXPENSE
        )

        # Add transfers for different combinations
        for idx, period in enumerate(periods, start=1):
            # Target: deposit1 + entity1 + income
            transfer_factory(
                period=period,
                category=income_category1,
                value=Decimal(f"{idx * 100}.00"),
                deposit=deposit1,
                entity=entity1,
            )
            # Other combinations (should be filtered out)
            transfer_factory(
                period=period,
                category=income_category1,
                value=Decimal(f"{idx * 50}.00"),
                deposit=deposit1,
                entity=entity2,
            )
            transfer_factory(
                period=period,
                category=income_category2,
                value=Decimal(f"{idx * 200}.00"),
                deposit=deposit2,
                entity=entity1,
            )
            transfer_factory(
                period=period,
                category=expense_category1,
                value=Decimal(f"{idx * 25}.00"),
                deposit=deposit1,
                entity=entity1,
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id),
            {
                "deposit": str(deposit1.id),
                "entity": str(entity1.id),
                "transfer_type": str(CategoryType.INCOME.value),
                "periods_count": 2,
            },
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 2
        assert response.data["xAxis"] == ["2024-02", "2024-03"]
        assert response.data["income_series"] == [Decimal("200.00"), Decimal("300.00")]
        assert response.data["expense_series"] == []

    def test_multiple_transfers_same_category_same_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple transfers in same category in same period.
        WHEN: TransfersInPeriodsChartApiView called by Wallet member.
        THEN: HTTP 200 - Response with correctly summed values.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        # Multiple income transfers
        transfer_factory(period=period, category=income_category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=income_category, value=Decimal("200.00"), deposit=deposit)
        transfer_factory(period=period, category=income_category, value=Decimal("300.00"), deposit=deposit)
        transfer_factory(period=period, category=income_category, value=Decimal("50.50"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(period_transfers_chart_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["income_series"] == [Decimal("650.50")]
        assert response.data["expense_series"] == [Decimal("0")]

    def test_entity_filter_nonexistent_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers.
        WHEN: TransfersInPeriodsChartApiView called with nonexistent entity ID.
        THEN: HTTP 200 - Response with zero values for all periods.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        entity = entity_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(
            period=period, category=income_category, value=Decimal("500.00"), deposit=deposit, entity=entity
        )

        api_client.force_authenticate(base_user)

        # Use a UUID that doesn't exist
        from entities.models import Entity

        nonexistent_id = Entity.objects.filter(wallet=wallet).order_by("-id").first().id + 1

        response = api_client.get(period_transfers_chart_url(wallet.id), {"entity": str(nonexistent_id)})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024"]
        assert response.data["expense_series"] == [Decimal("0")]
        assert response.data["income_series"] == [Decimal("0")]

    def test_transfer_type_with_periods_count(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple periods and transfers.
        WHEN: TransfersInPeriodsChartApiView called with transfer_type=INCOME and periods_count=2.
        THEN: HTTP 200 - Response with only income data for last 2 periods.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        for month in range(1, 5):
            period = period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # NOQA
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),
            )
            transfer_factory(
                period=period, category=income_category, value=Decimal(f"{month * 100}.00"), deposit=deposit
            )
            transfer_factory(
                period=period, category=expense_category, value=Decimal(f"{month * 50}.00"), deposit=deposit
            )

        api_client.force_authenticate(base_user)

        response = api_client.get(
            period_transfers_chart_url(wallet.id), {"transfer_type": str(CategoryType.INCOME.value), "periods_count": 2}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["2024-03", "2024-04"]
        assert response.data["income_series"] == [Decimal("300.00"), Decimal("400.00")]
        assert response.data["expense_series"] == []
