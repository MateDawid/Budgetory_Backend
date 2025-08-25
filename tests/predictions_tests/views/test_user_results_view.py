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


def users_results_url(budget_id: int, period_id: int):
    """Create and return a users results URL."""
    return reverse("predictions:users-results", args=[budget_id, period_id])


@pytest.mark.django_db
class TestUsersResultsAPIView:
    """Tests for UsersResultsAPIView."""

    def test_auth_required(
        self, api_client: APIClient, budget_factory: FactoryMetaClass, budgeting_period_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget and BudgetingPeriod instances in database.
        WHEN: UsersResultsAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        budget = budget_factory()
        period = budgeting_period_factory(budget=budget)

        response = api_client.get(users_results_url(budget.id, period.id))

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
        WHEN: UsersResultsAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        url = users_results_url(budget.id, period.id)
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
        WHEN: UsersResultsAPIView called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

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
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with user and common user data containing zero values returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

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
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with all budget members and common user data returned.
        """
        other_user = user_factory(username="otheruser")
        third_user = user_factory(username="thirduser")
        budget = budget_factory(members=[base_user, other_user, third_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

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
        WHEN: UsersResultsAPIView called by Budget member.
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

        response = api_client.get(users_results_url(budget.id, period.id))

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

    def test_get_users_results_with_period_expenses(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with members, BudgetingPeriod and Expenses for different users in database.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct period_expenses values for each user returned.
        """
        other_user = user_factory(username="otheruser")
        budget = budget_factory(members=[base_user, other_user])
        period = budgeting_period_factory(budget=budget)

        # Create categories for different users
        user_category_1 = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        user_category_2 = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        common_category = transfer_category_factory(budget=budget, owner=None, category_type=CategoryType.EXPENSE)

        # Create expenses
        expense_factory(period=period, category=user_category_1, value=Decimal("75.50"))
        expense_factory(period=period, category=user_category_1, value=Decimal("100"))
        expense_factory(period=period, category=user_category_2, value=Decimal("24.50"))
        expense_factory(period=period, category=common_category, value=Decimal("300.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user with expenses
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["period_expenses"] == "200.00"

        # Check common user with expenses
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["period_expenses"] == "300.00"

        # Check other user without expenses
        other_user_data = next(item for item in response.data if item["user_username"] == other_user.username)
        assert other_user_data["period_expenses"] == "0.00"

    def test_get_users_results_with_transfers_and_balance(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member, BudgetingPeriods and Transfers (incomes and expenses) for user in database.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct period_balance calculation returned.
        """
        budget = budget_factory(members=[base_user])
        previous_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        current_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        # Create categories
        income_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create transfers from previous periods (should be included in balance)
        transfer_factory(period=previous_period, category=income_category, value=Decimal("1000.00"))
        transfer_factory(period=previous_period, category=expense_category, value=Decimal("300.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check user balance (incomes - expenses)
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["period_balance"] == "700.00"  # 1000 - 300

    def test_get_users_results_response_structure(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member and BudgetingPeriod in database.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correct structure for each user returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

        for item in response.data:
            assert "user_username" in item
            assert "predictions_sum" in item
            assert "period_balance" in item
            assert "period_expenses" in item

            assert isinstance(item["predictions_sum"], str)
            assert isinstance(item["period_balance"], str)
            assert isinstance(item["period_expenses"], str)

    def test_get_users_results_common_user_format(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with member and BudgetingPeriod in database.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response includes common user with correct username format.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        # Find common user data
        common_data = next((item for item in response.data if "🏦 Common" in item["user_username"]), None)
        assert common_data is not None
        assert common_data["user_username"] == "🏦 Common"

    def test_error_period_does_not_exist(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget in database but BudgetingPeriod does not exist.
        WHEN: UsersResultsAPIView called with non-existent period_pk.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        non_existent_period_id = 99999
        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, non_existent_period_id))

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestUsersResultsAPIViewIntegration:
    """Integration tests for UsersResultsAPIView with complex scenarios."""

    def test_complete_budget_scenario(
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
    ):
        """
        GIVEN: Complete budget scenario with multiple users, periods, predictions, and transfers.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with accurate calculations for all users returned.
        """
        other_user = user_factory(username="otheruser")
        budget = budget_factory(members=[base_user, other_user])

        previous_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )
        current_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29)
        )

        # Create categories for different users and common
        user_income_cat = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.INCOME)
        user_expense_cat = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)
        other_income_cat = transfer_category_factory(budget=budget, owner=other_user, category_type=CategoryType.INCOME)
        common_expense_cat = transfer_category_factory(budget=budget, owner=None, category_type=CategoryType.EXPENSE)

        # Create predictions for current period
        expense_prediction_factory(period=current_period, category=user_expense_cat, current_plan=Decimal("400.00"))
        expense_prediction_factory(period=current_period, category=common_expense_cat, current_plan=Decimal("500.00"))

        # Create previous period transfers (for balance calculation)
        transfer_factory(period=previous_period, category=user_income_cat, value=Decimal("2000.00"))
        transfer_factory(period=previous_period, category=user_expense_cat, value=Decimal("800.00"))
        transfer_factory(period=previous_period, category=other_income_cat, value=Decimal("1500.00"))

        # Create current period expenses
        expense_factory(period=current_period, category=user_expense_cat, value=Decimal("200.00"))
        expense_factory(period=current_period, category=common_expense_cat, value=Decimal("150.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3  # base_user, other_user, common

        # Check base_user data
        user_data = next(item for item in response.data if item["user_username"] == base_user.username)
        assert user_data["predictions_sum"] == "400.00"  # User's prediction
        assert user_data["period_expenses"] == "200.00"  # Current period expense
        assert user_data["period_balance"] == "1200.00"  # 2000 income - 800 expense from previous

        # Check other_user data
        other_data = next(item for item in response.data if item["user_username"] == other_user.username)
        assert other_data["predictions_sum"] == "0.00"  # No predictions
        assert other_data["period_expenses"] == "0.00"  # No current period expenses
        assert other_data["period_balance"] == "1500.00"  # 1500 income from previous

        # Check common data
        common_data = next(item for item in response.data if item["user_username"] == "🏦 Common")
        assert common_data["predictions_sum"] == "500.00"  # Common prediction
        assert common_data["period_expenses"] == "150.00"  # Common current period expense
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
    ):
        """
        GIVEN: Budget with precise decimal values in predictions and expenses.
        WHEN: UsersResultsAPIView called by Budget member.
        THEN: HTTP 200 - Response with correctly formatted decimal values returned.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget)

        category = transfer_category_factory(budget=budget, owner=base_user, category_type=CategoryType.EXPENSE)

        # Create prediction and expense with precise decimals
        expense_prediction_factory(
            period=period, category=category, current_plan=Decimal("123.456")  # Should be rounded to 123.46
        )
        expense_factory(period=period, category=category, value=Decimal("67.899"))  # Should be rounded to 67.90

        api_client.force_authenticate(base_user)

        response = api_client.get(users_results_url(budget.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        user_data = next(item for item in response.data if item["user_username"] == base_user.username)

        # Check proper decimal formatting (2 decimal places)
        predictions_sum = Decimal(user_data["predictions_sum"])
        period_expenses = Decimal(user_data["period_expenses"])

        assert predictions_sum == Decimal("123.46")
        assert period_expenses == Decimal("67.90")
