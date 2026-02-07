from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from predictions.models import ExpensePrediction


def copy_predictions_url(wallet_id: int, period_id: int):
    """Create and return a copy predictions URL."""
    return reverse("predictions:copy-predictions-from-previous-period", args=[wallet_id, period_id])


@pytest.mark.django_db
class TestCopyPredictionsFromPreviousPeriodAPIView:
    """Tests for CopyPredictionsFromPreviousPeriodAPIView."""

    # ... existing tests ...

    def test_copy_predictions_already_exist_in_current_period(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with Periods and existing ExpensePredictions in current period.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: HTTP 400 returned with appropriate error message.
        """
        wallet = wallet_factory(owner=base_user)
        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        # Create prediction in current period
        expense_prediction_factory(period=current_period)

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data
            == "Can not copy Predictions from previous Period if any Prediction for current Period exists."
        )

    def test_successful_copy_predictions_from_previous_period(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with Periods and ExpensePredictions in previous period.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: HTTP 200 returned and predictions are copied successfully.
        """
        wallet = wallet_factory(owner=base_user)
        category1 = transfer_category_factory(wallet=wallet)
        category2 = transfer_category_factory(wallet=wallet)

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        # Create predictions in previous period
        prediction1 = expense_prediction_factory(
            period=previous_period, category=category1, current_plan=Decimal("100.50"), description="Test prediction 1"
        )
        prediction2 = expense_prediction_factory(
            period=previous_period, category=category2, current_plan=Decimal("200.75"), description="Test prediction 2"
        )

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == "Predictions copied successfully from previous Period."

        # Verify predictions were copied
        copied_predictions = ExpensePrediction.objects.filter(period=current_period)
        assert copied_predictions.count() == 2

        copied_prediction1 = copied_predictions.get(category=category1)
        assert copied_prediction1.current_plan == prediction1.current_plan
        assert copied_prediction1.description == prediction1.description

        copied_prediction2 = copied_predictions.get(category=category2)
        assert copied_prediction2.current_plan == prediction2.current_plan
        assert copied_prediction2.description == prediction2.description

    def test_copy_predictions_with_multiple_categories(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with multiple categories and predictions in previous period.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: All predictions are copied with correct category associations.
        """
        wallet = wallet_factory(owner=base_user)
        categories = [transfer_category_factory(wallet=wallet) for _ in range(5)]

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        # Create predictions for all categories
        original_predictions = []
        for i, category in enumerate(categories):
            prediction = expense_prediction_factory(
                period=previous_period,
                category=category,
                current_plan=Decimal(f"{(i+1) * 50}.{i*10}"),
                description=f"Prediction for category {i+1}",
            )
            original_predictions.append(prediction)

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify all predictions were copied
        copied_predictions = ExpensePrediction.objects.filter(period=current_period)
        assert copied_predictions.count() == 5

        for original_prediction in original_predictions:
            copied_prediction = copied_predictions.get(category=original_prediction.category)
            assert copied_prediction.current_plan == original_prediction.current_plan
            assert copied_prediction.description == original_prediction.description

    def test_copy_ignores_predictions_from_other_wallets(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with predictions in previous periods.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called for specific wallet.
        THEN: Only predictions from the specified wallet are copied.
        """
        # Target wallet
        wallet = wallet_factory(owner=base_user)
        category = transfer_category_factory(wallet=wallet)

        # Other wallet
        other_wallet = wallet_factory()
        other_category = transfer_category_factory(wallet=other_wallet)

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        other_previous_period = period_factory(
            wallet=other_wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31)
        )

        # Create prediction in target wallet
        expense_prediction_factory(
            period=previous_period,
            category=category,
            current_plan=Decimal("100.00"),
            description="Target wallet prediction",
        )

        # Create prediction in other wallet (should not be copied)
        expense_prediction_factory(
            period=other_previous_period,
            category=other_category,
            current_plan=Decimal("200.00"),
            description="Other wallet prediction",
        )

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        # Verify only one prediction was copied (from target wallet)
        copied_predictions = ExpensePrediction.objects.filter(period=current_period)
        assert copied_predictions.count() == 1
        assert copied_predictions.first().description == "Target wallet prediction"

    def test_copy_predictions_handles_none_values(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpensePredictions with None/null values in previous period.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: Predictions with None values are copied correctly.
        """
        wallet = wallet_factory(owner=base_user)
        category = transfer_category_factory(wallet=wallet)

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        # Create prediction with None description
        prediction = expense_prediction_factory(
            period=previous_period, category=category, current_plan=Decimal("100.00"), description=None
        )

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK

        copied_prediction = ExpensePrediction.objects.get(period=current_period)
        assert copied_prediction.description is None
        assert copied_prediction.current_plan == prediction.current_plan

    def test_copy_predictions_nonexistent_wallet(
        self,
        api_client: APIClient,
        base_user: User,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Nonexistent wallet ID.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: HTTP 403 returned (UserBelongsToWalletPermission fails).
        """
        period = period_factory()
        api_client.force_authenticate(base_user)
        url = copy_predictions_url(99999, period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_copy_predictions_nonexistent_period(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Nonexistent period ID but valid wallet.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: HTTP 200 returned with no predictions message.
        """
        wallet = wallet_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, 99999)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == "No predictions to copy from previous Period."

    @patch("predictions.models.ExpensePrediction.objects.bulk_create")
    def test_copy_predictions_database_error(
        self,
        mock_bulk_create,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Database error during bulk_create operation.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with POST.
        THEN: HTTP 500 returned with error message and transaction is rolled back.
        """
        mock_bulk_create.side_effect = Exception("Database connection error")

        wallet = wallet_factory(owner=base_user)
        category = transfer_category_factory(wallet=wallet)

        previous_period = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        current_period = period_factory(
            wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 29), previous_period=previous_period
        )

        expense_prediction_factory(period=previous_period, category=category, current_plan=Decimal("100.00"))

        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, current_period.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data == "Unexpected error raised on copying Predictions from previous Period."
        assert ExpensePrediction.objects.filter(period=current_period).count() == 0

    def test_copy_predictions_only_post_method_allowed(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Valid wallet and period.
        WHEN: CopyPredictionsFromPreviousPeriodAPIView endpoint called with GET/PUT/DELETE.
        THEN: HTTP 405 Method Not Allowed returned.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = copy_predictions_url(wallet.id, period.id)

        # Test GET method
        response = api_client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test PUT method
        response = api_client.put(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test DELETE method
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
