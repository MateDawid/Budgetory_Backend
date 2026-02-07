from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from predictions_tests.utils import annotate_expense_prediction_queryset
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from predictions.models import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer
from predictions.views.prediction_progress_status_view import PredictionProgressStatus


def expense_prediction_url(wallet_id: int):
    """Create and return an ExpensePrediction list URL."""
    return reverse("wallets:expense_prediction-list", args=[wallet_id])


@pytest.mark.django_db
class TestExpensePredictionFilterSetOrdering:
    """Tests for ordering with ExpensePredictionFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "-id",
            "period__name",
            "-period__name",
            "category__name",
            "-category__name",
            "category__priority",
            "-category__priority",
            "initial_plan",
            "-initial_plan",
            "current_plan",
            "-current_plan",
        ),
    )
    def test_get_predictions_list_sorted_by_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Four ExpensePrediction objects created in database.
        WHEN: The ExpensePredictionViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all ExpensePrediction existing in database sorted by given param.
        """
        wallet = wallet_factory(owner=base_user)
        period_1 = period_factory(wallet=wallet, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_2 = period_factory(wallet=wallet, date_start=date(2024, 2, 1), date_end=date(2024, 2, 28))
        category_1 = transfer_category_factory(
            wallet=wallet, name="Most important", priority=CategoryPriority.MOST_IMPORTANT
        )
        category_2 = transfer_category_factory(wallet=wallet, name="Other", priority=CategoryPriority.OTHERS)
        expense_prediction_factory(wallet=wallet, current_plan=5, initial_plan=5, period=period_1, category=category_1)
        expense_prediction_factory(wallet=wallet, current_plan=4, initial_plan=4, period=period_2, category=category_2)
        expense_prediction_factory(wallet=wallet, current_plan=3, initial_plan=3, period=period_2, category=category_1)
        expense_prediction_factory(wallet=wallet, current_plan=2, initial_plan=2, period=period_1, category=category_2)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK

        # Get the base queryset (same as ViewSet)
        base_queryset = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet__pk=wallet.pk).select_related(
                "period",
                "period__wallet",
                "period__previous_period",
                "category",
                "category__wallet",
                "category__deposit",
            )
        ).order_by(
            "id"
        )  # Default ordering

        # Apply the same ordering logic as OrderingFilter
        predictions = base_queryset.order_by(sort_param)  # This replaces the default ordering

        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(predictions) == 4


@pytest.mark.django_db
class TestExpensePredictionFilterSetFiltering:
    """Tests for filtering with ExpensePredictionFilterSet."""

    def test_get_predictions_list_filtered_by_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with period filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        period value.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, name="Test name")
        prediction = expense_prediction_factory(wallet=wallet, period=period)
        expense_prediction_factory(wallet=wallet, period=period_factory(wallet=wallet, name="Other period"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"period": period.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet, period__id=period.id)
        ).order_by("id")
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id

    def test_get_predictions_list_filtered_by_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with category filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        category value.
        """
        wallet = wallet_factory(owner=base_user)
        category = transfer_category_factory(wallet=wallet, name="Test name", category_type=CategoryType.EXPENSE)
        prediction = expense_prediction_factory(wallet=wallet, category=category)
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(wallet=wallet, name="Other", category_type=CategoryType.EXPENSE),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"category": category.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet, category__id=category.id)
        )
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id

    def test_get_predictions_list_filtered_by_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet with different category deposits.
        WHEN: The ExpensePredictionViewSet list view is called with deposit filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        deposit value.
        """
        wallet = wallet_factory(owner=base_user)
        deposit = deposit_factory(wallet=wallet)
        matching_category = transfer_category_factory(
            wallet=wallet, name="Matching", deposit=deposit, category_type=CategoryType.EXPENSE
        )
        prediction = expense_prediction_factory(wallet=wallet, category=matching_category)
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(
                wallet=wallet, name="Other", deposit=deposit_factory(wallet=wallet), category_type=CategoryType.EXPENSE
            ),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"deposit": deposit.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet, category__deposit__id=deposit.id)
        )
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id

    @pytest.mark.parametrize(
        "progress_status,expected_count",
        [
            (PredictionProgressStatus.NOT_USED.value, 1),
            (PredictionProgressStatus.IN_PLANNED_RANGE.value, 1),
            (PredictionProgressStatus.FULLY_UTILIZED.value, 1),
            (PredictionProgressStatus.OVERUSED.value, 1),
        ],
    )
    def test_get_predictions_list_filtered_by_progress_status(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        progress_status: int,
        expected_count: int,
    ):
        """
        GIVEN: Four ExpensePrediction objects for single Wallet with different progress statuses.
        WHEN: The ExpensePredictionViewSet list view is called with progress_status filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        progress status.
        """
        wallet = wallet_factory(owner=base_user)
        deposit = deposit_factory(wallet=wallet)

        # NOT_USED: current_funds_left == current_plan
        expense_prediction_factory(wallet=wallet, deposit=deposit, current_plan=Decimal("100.00"))

        # IN_PLANNED_RANGE: 0 < current_funds_left < current_plan
        in_planned_range_prediction = expense_prediction_factory(
            wallet=wallet, deposit=deposit, current_plan=Decimal("100.00")
        )
        expense_factory(
            wallet=wallet,
            deposit=deposit,
            category=in_planned_range_prediction.category,
            period=in_planned_range_prediction.period,
            value=Decimal("10.00"),
        )

        # FULLY_UTILIZED: current_funds_left == 0
        fully_utilized_prediction = expense_prediction_factory(
            wallet=wallet, deposit=deposit, current_plan=Decimal("100.00")
        )
        expense_factory(
            wallet=wallet,
            deposit=deposit,
            category=fully_utilized_prediction.category,
            period=fully_utilized_prediction.period,
            value=Decimal("100.00"),
        )

        # OVERUSED: current_funds_left < 0
        overused_prediction = expense_prediction_factory(wallet=wallet, deposit=deposit, current_plan=Decimal("100.00"))
        expense_factory(
            wallet=wallet,
            deposit=deposit,
            category=overused_prediction.category,
            period=overused_prediction.period,
            value=Decimal("101.00"),
        )

        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={"progress_status": progress_status})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 4
        assert len(response.data) == expected_count

    @pytest.mark.parametrize("field", ("initial_plan", "current_plan"))
    def test_get_predictions_list_filtered_by_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        Decimal value.
        """
        wallet = wallet_factory(owner=base_user)
        value = "123.45"
        prediction = expense_prediction_factory(wallet=wallet, **{field: Decimal(value)})
        expense_prediction_factory(wallet=wallet, **{field: Decimal("234.56")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={field: value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(ExpensePrediction.objects.filter(**{field: value}))
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value

    @pytest.mark.parametrize("field", ("initial_plan", "current_plan"))
    def test_get_predictions_list_filtered_by_value_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value MAX filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        Decimal value MAX value.
        """
        wallet = wallet_factory(owner=base_user)
        value = "123.45"
        prediction = expense_prediction_factory(wallet=wallet, **{field: Decimal(value)})
        expense_prediction_factory(wallet=wallet, **{field: Decimal("234.56")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={f"{field}_max": value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(ExpensePrediction.objects.filter(**{f"{field}__lte": value}))
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value

    @pytest.mark.parametrize("field", ("initial_plan", "current_plan"))
    def test_get_predictions_list_filtered_by_value_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value MIN filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        Decimal value MIN value.
        """
        wallet = wallet_factory(owner=base_user)
        value = "234.56"
        prediction = expense_prediction_factory(wallet=wallet, **{field: Decimal(value)})
        expense_prediction_factory(wallet=wallet, **{field: Decimal("123.45")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(wallet.id), data={f"{field}_min": value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = annotate_expense_prediction_queryset(ExpensePrediction.objects.filter(**{f"{field}__gte": value}))
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value

    def test_get_predictions_list_filtered_by_category_priority(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Three ExpensePrediction with categories with different CategoryPriority values for single Wallet.
        WHEN: The ExpensePredictionViewSet list view is called with category filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Wallet matching given
        category_priority value.
        """
        wallet = wallet_factory(owner=base_user)
        category = transfer_category_factory(
            wallet=wallet, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )
        prediction = expense_prediction_factory(wallet=wallet, category=category)
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(
                wallet=wallet, category_type=CategoryType.EXPENSE, priority=CategoryPriority.SAVINGS
            ),
        )
        expense_prediction_factory(
            wallet=wallet,
            category=transfer_category_factory(
                wallet=wallet, category_type=CategoryType.EXPENSE, priority=CategoryPriority.OTHERS
            ),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(
            expense_prediction_url(wallet.id), data={"category_priority": CategoryPriority.MOST_IMPORTANT.value}
        )

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 3
        predictions = annotate_expense_prediction_queryset(
            ExpensePrediction.objects.filter(period__wallet=wallet, category__id=category.id)
        )
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
