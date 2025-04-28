from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from predictions.models import ExpensePrediction
from predictions.serializers.expense_prediction_serializer import ExpensePredictionSerializer


def expense_prediction_url(budget_id: int):
    """Create and return an ExpensePrediction list URL."""
    return reverse("budgets:expense_prediction-list", args=[budget_id])


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
            "initial_value",
            "-initial_value",
            "current_value",
            "-current_value",
        ),
    )
    def test_get_predictions_list_sorted_by_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Four ExpensePrediction objects created in database.
        WHEN: The ExpensePredictionViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all ExpensePrediction existing in database sorted by given param.
        """
        budget = budget_factory(members=[base_user])
        period_1 = budgeting_period_factory(budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31))
        period_2 = budgeting_period_factory(budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 28))
        category_1 = transfer_category_factory(
            budget=budget, name="Most important", owner=None, priority=CategoryPriority.MOST_IMPORTANT
        )
        category_2 = transfer_category_factory(
            budget=budget, name="Other", owner=None, priority=CategoryPriority.OTHERS
        )
        expense_prediction_factory(
            budget=budget, current_value=5, initial_value=5, period=period_1, category=category_1
        )
        expense_prediction_factory(
            budget=budget, current_value=4, initial_value=4, period=period_2, category=category_2
        )
        expense_prediction_factory(
            budget=budget, current_value=3, initial_value=3, period=period_2, category=category_1
        )
        expense_prediction_factory(
            budget=budget, current_value=2, initial_value=2, period=period_1, category=category_2
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        predictions = (
            ExpensePrediction.objects.filter(period__budget__pk=budget.pk)
            .prefetch_related("period", "category")
            .order_by(sort_param)
        )
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(predictions) == 4
        assert response.data == serializer.data


@pytest.mark.django_db
class TestExpensePredictionFilterSetFiltering:
    """Tests for filtering with ExpensePredictionFilterSet."""

    def test_get_predictions_list_filtered_by_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with period filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        period value.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, name="Test name")
        prediction = expense_prediction_factory(budget=budget, period=period)
        expense_prediction_factory(budget=budget, period=budgeting_period_factory(budget=budget, name="Other period"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"period": period.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(period__budget=budget, period__id=period.id)
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
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with category filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        category value.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget, name="Test name", category_type=CategoryType.EXPENSE)
        prediction = expense_prediction_factory(budget=budget, category=category)
        expense_prediction_factory(
            budget=budget,
            category=transfer_category_factory(budget=budget, name="Other", category_type=CategoryType.EXPENSE),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"category": category.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(period__budget=budget, category__id=category.id)
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id

    @pytest.mark.parametrize("field", ("initial_value", "current_value"))
    def test_get_predictions_list_filtered_by_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        Decimal value.
        """
        budget = budget_factory(members=[base_user])
        value = "123.45"
        prediction = expense_prediction_factory(budget=budget, **{field: Decimal(value)})
        expense_prediction_factory(budget=budget, **{field: Decimal("234.56")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={field: value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(**{field: value})
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value

    @pytest.mark.parametrize("field", ("initial_value", "current_value"))
    def test_get_predictions_list_filtered_by_value_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value MAX filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        Decimal value MAX value.
        """
        budget = budget_factory(members=[base_user])
        value = "123.45"
        prediction = expense_prediction_factory(budget=budget, **{field: Decimal(value)})
        expense_prediction_factory(budget=budget, **{field: Decimal("234.56")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={f"{field}_max": value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(**{f"{field}__lte": value})
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value

    @pytest.mark.parametrize("field", ("initial_value", "current_value"))
    def test_get_predictions_list_filtered_by_value_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        field,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with Decimal value MIN filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        Decimal value MIN value.
        """
        budget = budget_factory(members=[base_user])
        value = "234.56"
        prediction = expense_prediction_factory(budget=budget, **{field: Decimal(value)})
        expense_prediction_factory(budget=budget, **{field: Decimal("123.45")})
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={f"{field}_min": value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(**{f"{field}__gte": value})
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == predictions.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == prediction.id
        assert response.data[0][field] == value
