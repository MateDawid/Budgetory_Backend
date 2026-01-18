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
from charts.views.deposits_in_periods_chart_view.services.deposits_transfers_sums_service import (
    get_deposits_transfers_sums_in_period,
)


def deposits_results_url(wallet_id: int) -> str:
    """Create and return a deposits results URL."""
    return reverse("charts:deposits-in-periods-chart", args=[wallet_id])


@pytest.mark.django_db
class TestDepositsInPeriodsChartAPIView:
    """Tests for DepositsInPeriodsChartAPIView."""

    def test_auth_required(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet instance in database.
        WHEN: DepositsInPeriodsChartAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositsInPeriodsChartAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = deposits_results_url(wallet.id)
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
        WHEN: DepositsInPeriodsChartAPIView called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_deposits_results_empty_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with no periods and no deposits in database.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_no_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposits but no periods in database.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_no_deposits(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods but no deposits in database.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_basic_scenario(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with periods and deposits but no transfers.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with periods on xAxis and deposits with zero balances in series.
        """
        wallet = wallet_factory(members=[base_user])
        period_factory(wallet=wallet, name="Jan 2024")
        period_factory(wallet=wallet, name="Feb 2024")
        deposit_factory(wallet=wallet, name="Checking Account")

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024"]
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["label"] == "Checking Account"
        assert response.data["series"][0]["data"] == [0.0, 0.0]
        assert "rgba(" in response.data["series"][0]["color"]

    def test_get_deposits_results_with_transfers(
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
        GIVEN: Wallet with periods, deposits, and transfers.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correct cumulative balance calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(
            wallet=wallet, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = period_factory(
            wallet=wallet, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )
        period3 = period_factory(
            wallet=wallet, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        # Create deposits
        user_daily_expenses_deposit = deposit_factory(wallet=wallet, name="User Daily Expenses")
        common_daily_expenses_deposit = deposit_factory(wallet=wallet, name="Common Daily Expenses")
        deposit_factory(wallet=wallet, name="Common Other")
        deposit_factory(wallet=wallet, name="User Savings")

        # Create categories
        user_income = transfer_category_factory(
            wallet=wallet, deposit=user_daily_expenses_deposit, category_type=CategoryType.INCOME
        )
        user_expense = transfer_category_factory(
            wallet=wallet, deposit=user_daily_expenses_deposit, category_type=CategoryType.EXPENSE
        )
        common_income = transfer_category_factory(
            wallet=wallet, deposit=common_daily_expenses_deposit, category_type=CategoryType.INCOME
        )
        common_expense = transfer_category_factory(
            wallet=wallet, deposit=common_daily_expenses_deposit, category_type=CategoryType.EXPENSE
        )

        # Transfers for Period 1
        transfer_factory(
            period=period1, category=user_income, value=Decimal("200.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period1, category=user_expense, value=Decimal("100.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period1, category=common_income, value=Decimal("400.00"), deposit=common_daily_expenses_deposit
        )
        transfer_factory(
            period=period1, category=common_expense, value=Decimal("200.00"), deposit=common_daily_expenses_deposit
        )

        # Transfers for Period 2
        transfer_factory(
            period=period2, category=user_income, value=Decimal("200.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period2, category=user_expense, value=Decimal("100.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period2, category=common_income, value=Decimal("400.00"), deposit=common_daily_expenses_deposit
        )
        transfer_factory(
            period=period2, category=common_expense, value=Decimal("200.00"), deposit=common_daily_expenses_deposit
        )

        # Transfers for Period 3
        transfer_factory(
            period=period3, category=user_income, value=Decimal("200.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period3, category=user_expense, value=Decimal("100.00"), deposit=user_daily_expenses_deposit
        )
        transfer_factory(
            period=period3, category=common_income, value=Decimal("400.00"), deposit=common_daily_expenses_deposit
        )
        transfer_factory(
            period=period3, category=common_expense, value=Decimal("200.00"), deposit=common_daily_expenses_deposit
        )

        api_client.force_authenticate(base_user)

        # Test without filtering - all deposits and periods
        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Jan 2024", "Feb 2024", "Mar 2024"]
        assert len(response.data["series"]) == 4

        # Find specific deposits in response
        user_daily_expenses_series = next(s for s in response.data["series"] if s["label"] == "User Daily Expenses")
        user_savings_series = next(s for s in response.data["series"] if s["label"] == "User Savings")
        common_daily_expenses_series = next(s for s in response.data["series"] if s["label"] == "Common Daily Expenses")
        common_other_series = next(s for s in response.data["series"] if s["label"] == "Common Other")

        # Verify calculations
        assert user_daily_expenses_series["data"] == [100.0, 200.0, 300.0]
        assert user_savings_series["data"] == [0.0, 0.0, 0.0]
        assert common_daily_expenses_series["data"] == [200.0, 400.0, 600.0]
        assert common_other_series["data"] == [0.0, 0.0, 0.0]

        # Test with period filtering
        response = api_client.get(deposits_results_url(wallet.id), {"period_from": period2.id, "period_to": period3.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Feb 2024", "Mar 2024"]

        # Test with specific deposit filtering
        response = api_client.get(deposits_results_url(wallet.id), {"deposit": user_daily_expenses_deposit.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["label"] == "User Daily Expenses"

    def test_large_dataset_performance_simulation(
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
        GIVEN: Wallet with many periods, deposits, and transfers to simulate real-world load.
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response returned efficiently with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])

        # Create 12 periods (full year)
        periods = []
        for month in range(1, 13):
            period = period_factory(
                wallet=wallet,
                name=f"2024-{month:02d}",  # noqa
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),  # Simplified for testing
            )
            periods.append(period)

        # Create multiple deposits
        deposits = []
        for i in range(5):
            deposit = deposit_factory(
                wallet=wallet,
                name=f"Account {i+1}",
            )
            transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
            transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
            deposits.append(deposit)

        # Create transfers for each period and deposit combination (realistic scenario)
        base_income = 1000
        base_expense = 300
        for i, period in enumerate(periods):
            for j, deposit in enumerate(deposits):
                # Varying income and expenses
                income_amount = base_income + (i * 50) + (j * 100)
                expense_amount = base_expense + (i * 10) + (j * 20)

                transfer_factory(
                    period=period,
                    category=deposit.transfer_categories.get(category_type=CategoryType.INCOME),
                    value=Decimal(str(income_amount)),
                    deposit=deposit,
                )
                transfer_factory(
                    period=period,
                    category=deposit.transfer_categories.get(category_type=CategoryType.EXPENSE),
                    value=Decimal(str(expense_amount)),
                    deposit=deposit,
                )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["xAxis"]) == 12  # All 12 periods
        assert len(response.data["series"]) == 5  # All 5 deposits

        # Verify that each deposit has data for all periods
        for series in response.data["series"]:
            assert len(series["data"]) == 12
            # Verify that balances are cumulative and increasing (since income > expense)
            for i in range(1, len(series["data"])):
                assert series["data"][i] >= series["data"][i - 1]

    def test_edge_cases_and_error_handling(
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
        GIVEN: Wallet with various edge cases (zero balances, negative balances, missing data).
        WHEN: DepositsInPeriodsChartAPIView called by Wallet member.
        THEN: HTTP 200 - Response handles edge cases gracefully with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(wallet=wallet, name="Period 1")
        period2 = period_factory(wallet=wallet, name="Period 2")

        # Deposits with different scenarios
        zero_balance_deposit = deposit_factory(wallet=wallet, name="Zero Balance")
        transfer_category_factory(wallet=wallet, deposit=zero_balance_deposit, category_type=CategoryType.EXPENSE)
        transfer_category_factory(wallet=wallet, deposit=zero_balance_deposit, category_type=CategoryType.INCOME)

        negative_deposit = deposit_factory(wallet=wallet, name="Negative Balance")
        transfer_category_factory(wallet=wallet, deposit=negative_deposit, category_type=CategoryType.EXPENSE)
        transfer_category_factory(wallet=wallet, deposit=negative_deposit, category_type=CategoryType.INCOME)

        normal_deposit = deposit_factory(wallet=wallet, name="Normal Balance")
        transfer_category_factory(wallet=wallet, deposit=normal_deposit, category_type=CategoryType.EXPENSE)
        transfer_category_factory(wallet=wallet, deposit=normal_deposit, category_type=CategoryType.INCOME)

        # Zero deposit: no transactions (should remain 0)
        # Negative deposit: only expenses
        transfer_factory(
            period=period1,
            category=negative_deposit.transfer_categories.get(category_type=CategoryType.EXPENSE),
            value=Decimal("500.00"),
            deposit=negative_deposit,
        )
        transfer_factory(
            period=period2,
            category=negative_deposit.transfer_categories.get(category_type=CategoryType.EXPENSE),
            value=Decimal("300.00"),
            deposit=negative_deposit,
        )

        # Normal deposit: income and expenses
        transfer_factory(
            period=period1,
            category=normal_deposit.transfer_categories.get(category_type=CategoryType.INCOME),
            value=Decimal("1000.00"),
            deposit=normal_deposit,
        )
        transfer_factory(
            period=period1,
            category=normal_deposit.transfer_categories.get(category_type=CategoryType.EXPENSE),
            value=Decimal("200.00"),
            deposit=normal_deposit,
        )
        transfer_factory(
            period=period2,
            category=normal_deposit.transfer_categories.get(category_type=CategoryType.INCOME),
            value=Decimal("500.00"),
            deposit=normal_deposit,
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 3

        # Find each deposit's data
        zero_series = next(s for s in response.data["series"] if s["label"] == "Zero Balance")
        negative_series = next(s for s in response.data["series"] if s["label"] == "Negative Balance")
        normal_series = next(s for s in response.data["series"] if s["label"] == "Normal Balance")

        # Verify calculations
        assert zero_series["data"] == [0.0, 0.0]  # No transactions
        assert negative_series["data"] == [-500.0, -800.0]  # Cumulative expenses
        assert normal_series["data"] == [800.0, 1300.0]  # P1: 1000-200=800, P2: 800+500=1300

    def test_empty_period_no_transfers(
        self,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Period with no transfers for specified deposits.
        WHEN: get_deposits_transfers_sums_in_period called for any transfer type.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {}

    def test_single_deposit_single_income_transfer(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Single deposit with one income transfer in period.
        WHEN: get_deposits_transfers_sums_in_period called for INCOME type.
        THEN: Dict with deposit_id and correct sum returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit.id: 500.0}

    def test_single_deposit_single_expense_transfer(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Single deposit with one expense transfer in period.
        WHEN: get_deposits_transfers_sums_in_period called for EXPENSE type.
        THEN: Dict with deposit_id and correct sum returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)
        transfer_factory(period=period, category=category, value=Decimal("250.00"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.EXPENSE,
        )

        assert result == {deposit.id: 250.0}

    def test_multiple_transfers_same_type_aggregation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple income transfers for same deposit in period.
        WHEN: get_deposits_transfers_sums_in_period called for INCOME type.
        THEN: Dict with deposit_id and aggregated sum returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.00"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("150.50"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit.id: 450.5}

    def test_wrong_transfer_type_filtering(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit with both income and expense transfers.
        WHEN: get_deposits_transfers_sums_in_period called for INCOME type only.
        THEN: Only income transfers summed, expenses ignored.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)

        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        transfer_factory(period=period, category=income_category, value=Decimal("500.00"), deposit=deposit)
        transfer_factory(period=period, category=expense_category, value=Decimal("300.00"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit.id: 500.0}

    def test_multiple_deposits_same_period(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple deposits with transfers in same period.
        WHEN: get_deposits_transfers_sums_in_period called with all deposit IDs.
        THEN: Dict with all deposit_ids and their respective sums returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        deposit1 = deposit_factory(wallet=wallet, name="Deposit 1")
        deposit2 = deposit_factory(wallet=wallet, name="Deposit 2")
        deposit3 = deposit_factory(wallet=wallet, name="Deposit 3")

        category1 = transfer_category_factory(wallet=wallet, deposit=deposit1, category_type=CategoryType.INCOME)
        category2 = transfer_category_factory(wallet=wallet, deposit=deposit2, category_type=CategoryType.INCOME)
        category3 = transfer_category_factory(wallet=wallet, deposit=deposit3, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=category1, value=Decimal("100.00"), deposit=deposit1)
        transfer_factory(period=period, category=category2, value=Decimal("200.00"), deposit=deposit2)
        transfer_factory(period=period, category=category3, value=Decimal("300.00"), deposit=deposit3)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit1.id, deposit2.id, deposit3.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit1.id: 100.0, deposit2.id: 200.0, deposit3.id: 300.0}

    def test_deposit_with_no_transfers_excluded(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple deposits, some with transfers and some without.
        WHEN: get_deposits_transfers_sums_in_period called.
        THEN: Only deposits with transfers appear in result dict.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        deposit_with_transfer = deposit_factory(wallet=wallet, name="With Transfer")
        deposit_without_transfer = deposit_factory(wallet=wallet, name="Without Transfer")

        category = transfer_category_factory(
            wallet=wallet, deposit=deposit_with_transfer, category_type=CategoryType.INCOME
        )
        transfer_factory(period=period, category=category, value=Decimal("500.00"), deposit=deposit_with_transfer)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit_with_transfer.id, deposit_without_transfer.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert deposit_with_transfer.id in result
        assert deposit_without_transfer.id not in result
        assert result[deposit_with_transfer.id] == 500.0

    def test_different_periods_isolation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Transfers in multiple periods for same deposit.
        WHEN: get_deposits_transfers_sums_in_period called for specific period.
        THEN: Only transfers from specified period included in sum.
        """
        wallet = wallet_factory(members=[base_user])
        period1 = period_factory(wallet=wallet, name="Jan 2024")
        period2 = period_factory(wallet=wallet, name="Feb 2024")

        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period1, category=category, value=Decimal("100.00"), deposit=deposit)
        transfer_factory(period=period2, category=category, value=Decimal("200.00"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period1.id, "name": period1.name, "date_end": period1.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit.id: 100.0}

    def test_different_wallets_isolation(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with deposits and transfers.
        WHEN: get_deposits_transfers_sums_in_period called for specific wallet.
        THEN: Only transfers from specified wallet included.
        """
        wallet1 = wallet_factory(members=[base_user])
        wallet2 = wallet_factory(members=[base_user])

        period1 = period_factory(wallet=wallet1, name="Jan 2024")
        period2 = period_factory(wallet=wallet2, name="Jan 2024")

        deposit1 = deposit_factory(wallet=wallet1)
        deposit2 = deposit_factory(wallet=wallet2)

        category1 = transfer_category_factory(wallet=wallet1, deposit=deposit1, category_type=CategoryType.INCOME)
        category2 = transfer_category_factory(wallet=wallet2, deposit=deposit2, category_type=CategoryType.INCOME)

        transfer_factory(period=period1, category=category1, value=Decimal("100.00"), deposit=deposit1)
        transfer_factory(period=period2, category=category2, value=Decimal("200.00"), deposit=deposit2)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet1.id,
            deposit_ids=[deposit1.id],
            period={"pk": period1.id, "name": period1.name, "date_end": period1.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit1.id: 100.0}
        assert deposit2.id not in result

    def test_decimal_precision_handling(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Transfers with precise decimal values.
        WHEN: get_deposits_transfers_sums_in_period called.
        THEN: Result maintains proper decimal precision as float.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)

        transfer_factory(period=period, category=category, value=Decimal("100.33"), deposit=deposit)
        transfer_factory(period=period, category=category, value=Decimal("200.67"), deposit=deposit)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {deposit.id: 301.0}

    def test_large_number_of_transfers(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit with many transfers in single period.
        WHEN: get_deposits_transfers_sums_in_period called.
        THEN: All transfers correctly aggregated.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")
        deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Create 50 transfers
        expected_sum = 0.0
        for i in range(50):
            value = Decimal(f"{(i + 1) * 10}.00")
            transfer_factory(period=period, category=category, value=value, deposit=deposit)
            expected_sum += float(value)

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[deposit.id],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.EXPENSE,
        )

        assert result == {deposit.id: expected_sum}

    def test_empty_deposit_ids_list(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Empty list of deposit IDs.
        WHEN: get_deposits_transfers_sums_in_period called.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {}

    def test_nonexistent_deposit_ids(
        self,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Non-existent deposit IDs.
        WHEN: get_deposits_transfers_sums_in_period called.
        THEN: Empty dict returned.
        """
        wallet = wallet_factory(members=[base_user])
        period = period_factory(wallet=wallet, name="Jan 2024")

        result = get_deposits_transfers_sums_in_period(
            wallet_pk=wallet.id,
            deposit_ids=[999999, 999998],
            period={"pk": period.id, "name": period.name, "date_end": period.date_end},
            transfer_type=CategoryType.INCOME,
        )

        assert result == {}
