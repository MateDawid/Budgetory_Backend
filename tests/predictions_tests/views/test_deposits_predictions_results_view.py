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


def deposits_predictions_results_url(wallet_id: int, period_id: int):
    """Create and return a deposits results URL."""
    return reverse("predictions:deposits-predictions-results", args=[wallet_id, period_id])


@pytest.mark.django_db
class TestDepositsPredictionsResultsAPIView:
    """Tests for DepositsPredictionsResultsAPIView."""

    def test_auth_required(
        self, api_client: APIClient, wallet_factory: FactoryMetaClass, period_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet and Period instances in database.
        WHEN: DepositsPredictionsResultsAPIView called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()
        period = period_factory(wallet=wallet)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: User's JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositsPredictionsResultsAPIView endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        url = deposits_predictions_results_url(wallet.id, period.id)
        jwt_access_token = get_jwt_access_token(user=base_user)

        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")

        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet and Period instances in database.
        WHEN: DepositsPredictionsResultsAPIView called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_deposits_results_for_no_data(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with single deposit and Period in database with no transfers or predictions.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with deposit data containing zero values returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit = deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1

        deposit_data = next(item for item in response.data if item["deposit_name"] == deposit.name)
        assert deposit_data["predictions_sum"] == "0.00"
        assert deposit_data["period_balance"] == "0.00"
        assert deposit_data["period_expenses"] == "0.00"
        assert deposit_data["funds_left_for_predictions"] == "0.00"
        assert deposit_data["funds_left_for_expenses"] == "0.00"

    def test_get_deposits_results_for_multiple_deposits(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple deposits and Period in database.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with all deposits data returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit_1 = deposit_factory(wallet=wallet)
        deposit_2 = deposit_factory(wallet=wallet)
        deposit_3 = deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        deposits_names = [item["deposit_name"] for item in response.data]
        assert deposit_1.name in deposits_names
        assert deposit_2.name in deposits_names
        assert deposit_3.name in deposits_names

    def test_get_deposits_results_with_expense_predictions(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with two Deposits, Period and ExpensePredictions for different deposits in database.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correct predictions_sum values for each deposit returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit_1 = deposit_factory(wallet=wallet)
        deposit_2 = deposit_factory(wallet=wallet)

        # Create categories
        category_1 = transfer_category_factory(wallet=wallet, deposit=deposit_1, category_type=CategoryType.EXPENSE)
        category_2 = transfer_category_factory(wallet=wallet, deposit=deposit_2, category_type=CategoryType.EXPENSE)

        # Create predictions
        expense_prediction_factory(period=period, category=category_1, current_plan=Decimal("150.00"))
        expense_prediction_factory(period=period, category=category_2, current_plan=Decimal("50.00"))

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        deposit_1_data = next(item for item in response.data if item["deposit_name"] == deposit_1.name)
        assert deposit_1_data["predictions_sum"] == "150.00"
        deposit_2_data = next(item for item in response.data if item["deposit_name"] == deposit_2.name)
        assert deposit_2_data["predictions_sum"] == "50.00"

    def test_get_deposits_results_with_transfers_and_balance_date_filtering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with Deposit, multiple Periods and Transfers with different dates.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correct period_balance calculation based on date filtering.
        """
        wallet = wallet_factory(owner=base_user)
        period_1 = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_2 = period_factory(wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29))
        current_period = period_factory(wallet=wallet, date_start=date(2024, 3, 1), date_end=date(2024, 3, 31))
        deposit = deposit_factory(wallet=wallet)

        # Create categories
        income_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.INCOME)
        expense_category = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=CategoryType.EXPENSE)

        # Create transfers in different periods
        # Period 1 transfers (should be included for expenses,
        # excluded for incomes due to date_start < current_period.date_start)
        transfer_factory(period=period_1, category=income_category, value=Decimal("1000.00"), deposit=deposit)
        transfer_factory(period=period_1, category=expense_category, value=Decimal("200.00"), deposit=deposit)

        # Period 2 transfers (should be included for expenses, excluded for incomes)
        transfer_factory(period=period_2, category=income_category, value=Decimal("500.00"), deposit=deposit)
        transfer_factory(period=period_2, category=expense_category, value=Decimal("100.00"), deposit=deposit)

        # Current period transfers (should be excluded as they are not before current period start)
        transfer_factory(period=current_period, category=income_category, value=Decimal("800.00"), deposit=deposit)
        transfer_factory(period=current_period, category=expense_category, value=Decimal("50.00"), deposit=deposit)

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK

        # Check deposit balance calculation
        # For expenses: date_start filter applies - periods 1 & 2 included (200 + 100 = 300)
        # For incomes: date_end filter applies - periods 1, 2 & 3 included (1000 + 500 + 800 = 2300)
        # Balance = 2300 - 300 = 2000
        deposit_data = next(item for item in response.data if item["deposit_name"] == deposit.name)
        assert deposit_data["period_balance"] == "2000.00"

    def test_get_deposits_results_response_structure(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with Deposit and Period in database.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correct structure for each user returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)
        assert len(response.data) == 1

        for item in response.data:
            assert "deposit_name" in item
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

    def test_error_period_does_not_exist(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database but Period does not exist.
        WHEN: DepositsPredictionsResultsAPIView called with non-existent period_pk.
        THEN: HTTP 404 returned.
        """
        wallet = wallet_factory(owner=base_user)
        deposit_factory(wallet=wallet)
        non_existent_period_id = 99999
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, non_existent_period_id))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.data["detail"] == "Period with given pk does not exist in Wallet."


@pytest.mark.django_db
class TestDepositsPredictionsResultsAPIViewIntegration:
    """Integration tests for DepositsPredictionsResultsAPIView with complex scenarios."""

    def test_complete_wallet_scenario_with_deposit_filtering(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Complete wallet scenario with multiple deposits, periods, predictions, transfers.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with accurate calculations for all deposits returned.
        """
        wallet = wallet_factory(owner=base_user)

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29))

        # Create deposits
        daily_expenses_deposit_1 = deposit_factory(wallet=wallet)
        daily_expenses_deposit_2 = deposit_factory(wallet=wallet)

        # Create categories for different deposits
        daily_expenses_deposit_1_income_category = transfer_category_factory(
            wallet=wallet, deposit=daily_expenses_deposit_1, category_type=CategoryType.INCOME
        )
        daily_expenses_deposit_1_expense_category = transfer_category_factory(
            wallet=wallet, deposit=daily_expenses_deposit_1, category_type=CategoryType.EXPENSE
        )
        daily_expenses_deposit_2_income_category = transfer_category_factory(
            wallet=wallet, deposit=daily_expenses_deposit_2, category_type=CategoryType.INCOME
        )

        # Create predictions for current period
        expense_prediction_factory(
            period=current_period, category=daily_expenses_deposit_1_expense_category, current_plan=Decimal("400.00")
        )

        # Create previous period transfers (for balance calculation)
        transfer_factory(
            period=previous_period,
            category=daily_expenses_deposit_1_income_category,
            value=Decimal("2000.00"),
            deposit=daily_expenses_deposit_1,
        )
        transfer_factory(
            period=previous_period,
            category=daily_expenses_deposit_1_expense_category,
            value=Decimal("800.00"),
            deposit=daily_expenses_deposit_1,
        )
        transfer_factory(
            period=previous_period,
            category=daily_expenses_deposit_2_income_category,
            value=Decimal("1500.00"),
            deposit=daily_expenses_deposit_2,
        )

        # Create current period expenses
        expense_factory(
            period=current_period,
            category=daily_expenses_deposit_1_expense_category,
            value=Decimal("200.00"),
            deposit=daily_expenses_deposit_1,
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_predictions_results_url(wallet.id, current_period.id))

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

        deposit_1_data = next(item for item in response.data if item["deposit_name"] == daily_expenses_deposit_1.name)
        assert deposit_1_data["predictions_sum"] == "400.00"  # User's prediction
        assert deposit_1_data["period_expenses"] == "200.00"  # Current period expense
        assert deposit_1_data["period_balance"] == "1200.00"  # 2000 income - 800 expense from previous

        deposit_2_data = next(item for item in response.data if item["deposit_name"] == daily_expenses_deposit_2.name)
        assert deposit_2_data["predictions_sum"] == "0.00"  # No predictions
        assert deposit_2_data["period_expenses"] == "0.00"  # No current period expenses
        assert deposit_2_data["period_balance"] == "1500.00"  # 1500 income from previous

    def test_decimal_precision_handling(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with precise decimal values in predictions and expenses.
        WHEN: DepositsPredictionsResultsAPIView called by Wallet member.
        THEN: HTTP 200 - Response with correctly formatted decimal values returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)

        entity = entity_factory(wallet=wallet)
        daily_deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=daily_deposit, category_type=CategoryType.EXPENSE)

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

        response = api_client.get(deposits_predictions_results_url(wallet.id, period.id))

        assert response.status_code == status.HTTP_200_OK

        deposit_data = next(item for item in response.data if item["deposit_name"] == daily_deposit.name)

        # The values should maintain their precision but be formatted with 2 decimal places
        assert deposit_data["predictions_sum"] == "123.46"  # Rounded to 2 decimal places
        assert deposit_data["period_expenses"] == "67.90"  # Rounded to 2 decimal places
