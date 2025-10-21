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


def deposits_predictions_results_url(budget_id: int, period_id: int):
    """Create and return a users results URL."""
    return reverse("predictions:deposits-predictions-results", args=[budget_id, period_id])


@pytest.mark.django_db
class TestDepositsPredictionsResultsAPIView:
    """Tests for DepositsPredictionsResultsAPIView."""

    def test_auth_required(
        self, api_client: APIClient, budget_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget and BudgetingPeriod instances in database.
        WHEN: DepositsPredictionsResultsAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        budget = budget_factory()
        period = budgeting_period_factory(budget=budget)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositsPredictionsResultsAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        url = deposits_predictions_results_url(budget.id, period.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget and BudgetingPeriod instances in database.
        WHEN: DepositsPredictionsResultsAPIView called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_users_results_empty_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with single member and BudgetingPeriod in database with no transfers or predictions.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with user and common user data containing zero values returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2  # Common user + base_user

        # Check common user (should be first due to id=0)
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["predictions_sum"] == "0.00"
        assert common_data["period_balance"] == "0.00"
        assert common_data["period_expenses"] == "0.00"

        # Check regular user
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["predictions_sum"] == "0.00"
        assert user_data["period_balance"] == "0.00"
        assert user_data["period_expenses"] == "0.00"

    def test_get_users_results_with_multiple_members(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple members and BudgetingPeriod in database.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with all budget members and common user data returned.
        """
        other_user = user_factory(username="otheruser")
        third_user = user_factory(username="thirduser")
        budget = budget_factory(members=[base_user, other_user, third_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 4  # Common user + 3 members

        usernames = [item["user_username"] for item in response.data]
        assert "🏦 Common" in usernames
        assert base_user.username in usernames
        assert other_user.username in usernames
        assert third_user.username in usernames

    def test_get_users_results_with_expense_predictions(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with members, BudgetingPeriod and ExpensePredictions for different users in database.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct predictions_sum values for each user returned.
        """
        other_user = user_factory(username="otheruser")
        budget = budget_factory(members=[base_user, other_user])
        period = budgeting_period_factory(budget=budget)

        # Create categories for different users
        user_category_1 = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        user_category_2 = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        common_category = transfer_category_factory(budget=budget, owner=None, category_type=CategoryType.EXPENSE)

        # Create predictions
        expense_prediction_factory(period=period, category=user_category_1, current_plan=Decimal("150.00"))
        expense_prediction_factory(period=period, category=user_category_2, current_plan=Decimal("50.00"))
        expense_prediction_factory(period=period, category=common_category, current_plan=Decimal("300.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user with prediction
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["predictions_sum"] == "200.00"

        # Check common user with prediction
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["predictions_sum"] == "300.00"

        # Check other user without predictions
        other_user_data = next(item for item in response.data if item["user_username"] == other_user.username)
        assert other_user_data["predictions_sum"] == "0.00"

    def test_get_users_results_with_period_expenses_daily_expenses_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with members, BudgetingPeriod and Expenses for different users with different deposit types.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct period_expenses values (only DAILY_EXPENSES deposits counted).
        """
        other_user = user_factory(username="otheruser")
        budget = budget_factory(members=[base_user, other_user])
        period = budgeting_period_factory(budget=budget)

        # Create deposits with different types
        daily_deposit_user = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.DAILY_EXPENSES)
        daily_deposit_common = deposit_factory(budget=budget, owner=None, deposit_type=DepositType.DAILY_EXPENSES)
        savings_deposit_user = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.SAVINGS)

        # Create categories
        user_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        common_category = transfer_category_factory(budget=budget, owner=None, category_type=CategoryType.EXPENSE)

        # Create expenses with different deposit types
        expense_factory(period=period, category=user_category, value=Decimal("100.00"), deposit=daily_deposit_user)
        expense_factory(
            period=period, category=user_category, value=Decimal("50.00"), deposit=savings_deposit_user
        )  # Should NOT be counted
        expense_factory(period=period, category=common_category, value=Decimal("200.00"), deposit=daily_deposit_common)

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user expenses (only DAILY_EXPENSES should be counted)
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["period_expenses"] == "100.00"  # Only the daily expenses deposit

        # Check common user expenses
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["period_expenses"] == "200.00"

        # Check other user without expenses
        other_user_data = next(item for item in response.data if item["user_username"] == other_user.username)
        assert other_user_data["period_expenses"] == "0.00"

    def test_get_users_results_with_transfers_and_balance_date_filtering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member, multiple BudgetingPeriods and Transfers with different dates.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct period_balance calculation based on date filtering.
        """
        budget = budget_factory(members=[base_user])

        # Create periods with specific dates
        period_1 = budgeting_period_factory(budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_2 = budgeting_period_factory(budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29))
        current_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 3, 1), date_end=date(2024, 3, 31)
        )

        # Create daily expenses deposit
        daily_deposit = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.DAILY_EXPENSES)

        # Create categories
        income_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create transfers in different periods
        # Period 1 transfers (should be included for expenses,
        # excluded for incomes due to date_start < current_period.date_start)
        transfer_factory(period=period_1, category=income_category, value=Decimal("1000.00"), deposit=daily_deposit)
        transfer_factory(period=period_1, category=expense_category, value=Decimal("200.00"), deposit=daily_deposit)

        # Period 2 transfers (should be included for expenses, excluded for incomes)
        transfer_factory(period=period_2, category=income_category, value=Decimal("500.00"), deposit=daily_deposit)
        transfer_factory(period=period_2, category=expense_category, value=Decimal("100.00"), deposit=daily_deposit)

        # Current period transfers (should be excluded as they are not before current period start)
        transfer_factory(
            period=current_period, category=income_category, value=Decimal("800.00"), deposit=daily_deposit
        )
        transfer_factory(
            period=current_period, category=expense_category, value=Decimal("50.00"), deposit=daily_deposit
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user balance calculation
        # For expenses: date_start filter applies - periods 1 & 2 included (200 + 100 = 300)
        # For incomes: date_end filter applies - periods 1, 2 & 3 included (1000 + 500 + 800 = 2300)
        # Balance = 2300 - 300 = 2000
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["period_balance"] == "2000.00"

    def test_get_users_results_with_transfers_daily_expenses_deposit_only(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member, BudgetingPeriods and Transfers with different deposit types.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with period_balance calculation only including DAILY_EXPENSES deposits.
        """
        budget = budget_factory(members=[base_user])
        previous_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        current_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        # Create deposits with different types
        daily_deposit = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.DAILY_EXPENSES)
        savings_deposit = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.SAVINGS)

        # Create categories
        income_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create transfers with different deposit types
        transfer_factory(
            period=previous_period, category=income_category, value=Decimal("1000.00"), deposit=daily_deposit
        )
        transfer_factory(
            period=previous_period, category=income_category, value=Decimal("500.00"), deposit=savings_deposit
        )  # Should NOT be counted
        transfer_factory(
            period=previous_period, category=expense_category, value=Decimal("300.00"), deposit=daily_deposit
        )
        transfer_factory(
            period=previous_period, category=expense_category, value=Decimal("200.00"), deposit=savings_deposit
        )  # Should NOT be counted

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user balance (only DAILY_EXPENSES deposits: 1000 income - 300 expense = 700)
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["period_balance"] == "700.00"

    def test_get_users_results_response_structure(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member and BudgetingPeriod in database.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct structure for each user returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        for item in response.data:
            assert "user_username" in item
            assert "predictions_sum" in item
            assert "period_balance" in item
            assert "period_expenses" in item

            # Check that all values are properly formatted as strings with 2 decimal places
            assert isinstance(item["predictions_sum"], str)
            assert isinstance(item["period_balance"], str)
            assert isinstance(item["period_expenses"], str)

            # Verify decimal format
            assert len(item["predictions_sum"].split(".")[-1]) == 2
            assert len(item["period_balance"].split(".")[-1]) == 2
            assert len(item["period_expenses"].split(".")[-1]) == 2

    def test_get_users_results_common_user_format(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member and BudgetingPeriod in database.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response includes common user with correct username format.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        # Find common user data
        common_data = next((item for item in response.data if "🏦 Common" in item["user_username"]), None)
        assert common_data is not None
        assert common_data["user_username"] == "🏦 Common"

    def test_get_users_results_ordering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with multiple members and BudgetingPeriod in database.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with users ordered by ID (common user first with id=0).
        """
        other_user = user_factory(
            username="zuser"
        )  # Username starting with 'z' to test that ordering is by ID, not username
        budget = budget_factory(members=[base_user, other_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 3

        # Common user should be first (id=0)
        assert response.data[0]["user_username"] == "🏦 Common"

    def test_error_period_does_not_exist(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database but BudgetingPeriod does not exist.
        WHEN: DepositsPredictionsResultsAPIView called with non-existent period_pk.
        THEN: HTTP 200 returned with zero values.
        """
        budget = budget_factory(members=[base_user])
        non_existent_period_id = 99999
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, non_existent_period_id))

        assert response.status_code == status.HTTP_200_OK

        # Should return users with zero values when period doesn't exist
        assert len(response.data) == 2  # base_user + common
        for item in response.data:
            assert item["predictions_sum"] == "0.00"
            assert item["period_balance"] == "0.00"
            assert item["period_expenses"] == "0.00"


@pytest.mark.django_db
class TestDepositsPredictionsResultsAPIViewIntegration:
    """Integration tests for DepositsPredictionsResultsAPIView with complex scenarios."""

    def test_complete_budget_scenario_with_deposit_filtering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Complete budget scenario with multiple users, periods, predictions, transfers
        and different deposit types.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with accurate calculations for all users returned (only DAILY_EXPENSES
        deposits counted).
        """
        other_user = user_factory(username="otheruser")
        budget = budget_factory(members=[base_user, other_user])

        previous_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        current_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        # Create deposits with different types
        daily_deposit_user = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.DAILY_EXPENSES)
        daily_deposit_other = deposit_factory(budget=budget, owner=other_user, deposit_type=DepositType.DAILY_EXPENSES)
        daily_deposit_common = deposit_factory(budget=budget, owner=None, deposit_type=DepositType.DAILY_EXPENSES)
        savings_deposit_user = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.SAVINGS)

        # Create categories for different users and common
        user_income_cat = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        user_expense_cat = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        other_income_cat = transfer_category_factory(budget=budget, owner=other_user, category_type=CategoryType.INCOME)
        common_expense_cat = transfer_category_factory(budget=budget, owner=None, category_type=CategoryType.EXPENSE)

        # Create predictions for current period
        expense_prediction_factory(period=current_period, category=user_expense_cat, current_plan=Decimal("400.00"))
        expense_prediction_factory(period=current_period, category=common_expense_cat, current_plan=Decimal("500.00"))

        # Create previous period transfers (for balance calculation) - mix of deposit types
        transfer_factory(
            period=previous_period, category=user_income_cat, value=Decimal("2000.00"), deposit=daily_deposit_user
        )
        transfer_factory(
            period=previous_period, category=user_income_cat, value=Decimal("1000.00"), deposit=savings_deposit_user
        )  # Should NOT be counted
        transfer_factory(
            period=previous_period, category=user_expense_cat, value=Decimal("800.00"), deposit=daily_deposit_user
        )
        transfer_factory(
            period=previous_period, category=other_income_cat, value=Decimal("1500.00"), deposit=daily_deposit_other
        )

        # Create current period expenses (only daily expenses counted)
        expense_factory(
            period=current_period, category=user_expense_cat, value=Decimal("200.00"), deposit=daily_deposit_user
        )
        expense_factory(
            period=current_period, category=user_expense_cat, value=Decimal("100.00"), deposit=savings_deposit_user
        )  # Should NOT be counted
        expense_factory(
            period=current_period, category=common_expense_cat, value=Decimal("150.00"), deposit=daily_deposit_common
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # base_user, other_user, common

        # Check base_user data (only DAILY_EXPENSES deposits counted)
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["predictions_sum"] == "400.00"  # User's prediction
        assert user_data["period_expenses"] == "200.00"  # Current period expense (only daily expenses)
        assert user_data["period_balance"] == "1200.00"  # 2000 income - 800 expense from previous (only daily expenses)

        # Check other_user data
        other_data = next(item for item in response.data if item["user_username"] == other_user.username)
        assert other_data["predictions_sum"] == "0.00"  # No predictions
        assert other_data["period_expenses"] == "0.00"  # No current period expenses
        assert other_data["period_balance"] == "1500.00"  # 1500 income from previous (daily expenses)

        # Check common data
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["predictions_sum"] == "500.00"  # Common prediction
        assert common_data["period_expenses"] == "150.00"  # Common current period expense (daily expenses)
        assert common_data["period_balance"] == "0.00"  # No previous transfers

    def test_decimal_precision_handling(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with precise decimal values in predictions and expenses.
        WHEN: DepositsPredictionsResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correctly formatted decimal values returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)

        # Create entity
        entity = entity_factory(budget=budget)

        # Create daily expenses deposit
        daily_deposit = deposit_factory(budget=budget, owner=base_user, deposit_type=DepositType.DAILY_EXPENSES)

        category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create prediction and expense with precise decimals
        expense_prediction_factory(
            period=period, category=category, current_plan=Decimal("123.456")  # Should be handled by Decimal formatting
        )
        expense_factory(
            period=period,
            category=category,
            value=Decimal("67.899"),  # Should be handled by Decimal formatting
            deposit=daily_deposit,
            entity=entity,
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        user_data = next(item for item in response.data if item["user_username"] == base_user.username)

        # The values should maintain their precision but be formatted with 2 decimal places
        assert user_data["predictions_sum"] == "123.46"  # Rounded to 2 decimal places
        assert user_data["period_expenses"] == "67.90"  # Rounded to 2 decimal places
