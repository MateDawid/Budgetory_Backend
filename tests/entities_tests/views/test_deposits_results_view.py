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
from entities.models.choices.deposit_type import DepositType


def deposits_results_url(budget_id: int) -> str:
    """Create and return a deposits results URL."""
    return reverse("entities:deposits-results", args=[budget_id])


@pytest.mark.django_db
class TestDepositsResultsAPIView:
    """Tests for DepositsResultsAPIView."""

    def test_auth_required(self, api_client: APIClient, budget_factory: FactoryMetaClass):
        """
        GIVEN: Budget instance in database.
        WHEN: DepositsResultsAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        budget = budget_factory()

        response = api_client.get(deposits_results_url(budget.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositsResultsAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = deposits_results_url(budget.id)
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
        WHEN: DepositsResultsAPIView called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_deposits_results_empty_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with no periods and no deposits in database.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_no_periods(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with deposits but no periods in database.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        budget = budget_factory(members=[base_user])
        deposit_factory(budget=budget, owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_no_deposits(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods but no deposits in database.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with empty xAxis and series arrays returned.
        """
        budget = budget_factory(members=[base_user])
        budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == []
        assert response.data["series"] == []

    def test_get_deposits_results_basic_scenario(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods and deposits but no transfers.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with periods on xAxis and deposits with zero balances in series.
        """
        budget = budget_factory(members=[base_user])
        budgeting_period_factory(budget=budget, name="Jan 2024")
        budgeting_period_factory(budget=budget, name="Feb 2024")
        deposit_factory(budget=budget, owner=base_user, name="Checking Account")

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

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
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with periods, deposits, and transfers.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct cumulative balance calculations.
        """
        budget = budget_factory(members=[base_user])
        period1 = budgeting_period_factory(
            budget=budget, name="Jan 2024", date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        period2 = budgeting_period_factory(
            budget=budget, name="Feb 2024", date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )
        period3 = budgeting_period_factory(
            budget=budget, name="Mar 2024", date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        # Create deposits with different types and owners
        user_daily_expenses_deposit = deposit_factory(
            budget=budget, owner=base_user, name="User Daily Expenses", deposit_type=DepositType.DAILY_EXPENSES
        )
        common_daily_expenses_deposit = deposit_factory(
            budget=budget, owner=None, name="Common Daily Expenses", deposit_type=DepositType.DAILY_EXPENSES
        )
        deposit_factory(budget=budget, owner=None, name="Common Other", deposit_type=DepositType.OTHER)
        deposit_factory(budget=budget, owner=base_user, name="User Savings", deposit_type=DepositType.SAVINGS)

        # Create categories
        user_income = transfer_category_factory(
            budget=budget, deposit=user_daily_expenses_deposit, category_type=CategoryType.INCOME
        )
        user_expense = transfer_category_factory(
            budget=budget, deposit=user_daily_expenses_deposit, category_type=CategoryType.EXPENSE
        )
        common_income = transfer_category_factory(
            budget=budget, deposit=common_daily_expenses_deposit, category_type=CategoryType.INCOME
        )
        common_expense = transfer_category_factory(
            budget=budget, deposit=common_daily_expenses_deposit, category_type=CategoryType.EXPENSE
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
        response = api_client.get(deposits_results_url(budget.id))

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

        # Test with deposit type filtering
        response = api_client.get(deposits_results_url(budget.id), {"deposit_type": DepositType.DAILY_EXPENSES})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 2  # Only daily expenses deposits
        deposit_labels = [s["label"] for s in response.data["series"]]
        assert "User Daily Expenses" in deposit_labels
        assert "User Savings" not in deposit_labels
        assert "Common Daily Expenses" in deposit_labels
        assert "Common Other" not in deposit_labels

        # Test with period filtering
        response = api_client.get(deposits_results_url(budget.id), {"period_from": period2.id, "period_to": period3.id})

        assert response.status_code == status.HTTP_200_OK
        assert response.data["xAxis"] == ["Feb 2024", "Mar 2024"]

        # Test with specific deposit filtering
        response = api_client.get(deposits_results_url(budget.id), {"deposit": user_daily_expenses_deposit.id})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["series"]) == 1
        assert response.data["series"][0]["label"] == "User Daily Expenses"

    def test_large_dataset_performance_simulation(
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
        GIVEN: Budget with many periods, deposits, and transfers to simulate real-world load.
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response returned efficiently with correct calculations.
        """
        budget = budget_factory(members=[base_user])

        # Create 12 periods (full year)
        periods = []
        for month in range(1, 13):
            period = budgeting_period_factory(
                budget=budget,
                name=f"2024-{month:02d}",  # noqa
                date_start=date(2024, month, 1),
                date_end=date(2024, month, 28),  # Simplified for testing
            )
            periods.append(period)

        # Create multiple deposits
        deposits = []
        for i in range(5):
            deposit = deposit_factory(
                budget=budget,
                owner=base_user,
                name=f"Account {i+1}",
                deposit_type=DepositType.DAILY_EXPENSES if i % 2 == 0 else DepositType.SAVINGS,
            )
            deposits.append(deposit)

        # Create categories
        income_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create transfers for each period and deposit combination (realistic scenario)
        base_income = 1000
        base_expense = 300
        for i, period in enumerate(periods):
            for j, deposit in enumerate(deposits):
                # Varying income and expenses
                income_amount = base_income + (i * 50) + (j * 100)
                expense_amount = base_expense + (i * 10) + (j * 20)

                transfer_factory(
                    period=period, category=income_category, value=Decimal(str(income_amount)), deposit=deposit
                )
                transfer_factory(
                    period=period, category=expense_category, value=Decimal(str(expense_amount)), deposit=deposit
                )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

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
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with various edge cases (zero balances, negative balances, missing data).
        WHEN: DepositsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response handles edge cases gracefully with correct calculations.
        """
        budget = budget_factory(members=[base_user])
        period1 = budgeting_period_factory(budget=budget, name="Period 1")
        period2 = budgeting_period_factory(budget=budget, name="Period 2")

        # Deposits with different scenarios
        deposit_factory(budget=budget, owner=base_user, name="Zero Balance")
        negative_deposit = deposit_factory(budget=budget, owner=base_user, name="Negative Balance")
        normal_deposit = deposit_factory(budget=budget, owner=base_user, name="Normal Balance")

        expense_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        income_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)

        # Zero deposit: no transactions (should remain 0)
        # Negative deposit: only expenses
        transfer_factory(period=period1, category=expense_category, value=Decimal("500.00"), deposit=negative_deposit)
        transfer_factory(period=period2, category=expense_category, value=Decimal("300.00"), deposit=negative_deposit)

        # Normal deposit: income and expenses
        transfer_factory(period=period1, category=income_category, value=Decimal("1000.00"), deposit=normal_deposit)
        transfer_factory(period=period1, category=expense_category, value=Decimal("200.00"), deposit=normal_deposit)
        transfer_factory(period=period2, category=income_category, value=Decimal("500.00"), deposit=normal_deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_results_url(budget.id))

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
