from datetime import date

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.transfer_category_choices import ExpenseCategoryPriority
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
            "category__priority",
            "-category__priority",
            "category__name",
            "-category__name",
            "value",
            "-value",
        ),
    )
    def test_get_predictions_list_sorted_by_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Four ExpensePrediction objects created in database.
        WHEN: The ExpensePredictionViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all ExpensePrediction existing in database sorted by given param.
        """
        budget = budget_factory(owner=base_user)
        period_1 = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=False
        )
        period_2 = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 28), is_active=True
        )
        category_1 = expense_category_factory(
            budget=budget, name="Most important", owner=None, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        )
        category_2 = expense_category_factory(
            budget=budget, name="Other", owner=None, priority=ExpenseCategoryPriority.OTHERS
        )
        expense_prediction_factory(budget=budget, value=5, period=period_1, category=category_1)
        expense_prediction_factory(budget=budget, value=4, period=period_2, category=category_2)
        expense_prediction_factory(budget=budget, value=3, period=period_2, category=category_1)
        expense_prediction_factory(budget=budget, value=2, period=period_1, category=category_2)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        predictions = (
            ExpensePrediction.objects.filter(period__budget__pk=budget.pk)
            .prefetch_related("period", "category")
            .order_by(sort_param)
        )
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(predictions) == 4
        assert response.data["results"] == serializer.data

    def test_get_categories_list_sorted_by_two_params(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Five ExpensePrediction objects created in database.
        WHEN: The ExpensePredictionViewSet list view is called with two sorting params by given params.
        THEN: Response must contain all ExpensePrediction existing in database sorted by given params.
        """
        budget = budget_factory(owner=base_user)
        period_1 = budgeting_period_factory(
            budget=budget, date_start=date(2024, 1, 1), date_end=date(2024, 1, 31), is_active=False
        )
        period_2 = budgeting_period_factory(
            budget=budget, date_start=date(2024, 2, 1), date_end=date(2024, 2, 28), is_active=True
        )
        category_1 = expense_category_factory(
            budget=budget, name="Most important", owner=None, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        )
        category_2 = expense_category_factory(
            budget=budget, name="Other", owner=None, priority=ExpenseCategoryPriority.OTHERS
        )
        expense_prediction_factory(budget=budget, value=5, period=period_1, category=category_1)
        expense_prediction_factory(budget=budget, value=4, period=period_2, category=category_2)
        expense_prediction_factory(budget=budget, value=3, period=period_2, category=category_1)
        expense_prediction_factory(budget=budget, value=2, period=period_1, category=category_2)
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"ordering": "period__name, -category__name"})

        assert response.status_code == status.HTTP_200_OK
        predictions = (
            ExpensePrediction.objects.filter(period__budget__pk=budget.pk)
            .prefetch_related("period", "category")
            .order_by("period__name", "-category__name")
        )
        serializer = ExpensePredictionSerializer(predictions, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(predictions) == 4
        assert response.data["results"] == serializer.data


@pytest.mark.django_db
class TestExpensePredictionFilterSetFiltering:
    """Tests for filtering with ExpensePredictionFilterSet."""

    def test_get_predictions_list_filtered_by_period_id(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with period_id filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        period_id value.
        """
        budget = budget_factory(owner=base_user)
        period = budgeting_period_factory(budget=budget, name="Test name")
        prediction = expense_prediction_factory(budget=budget, period=period)
        expense_prediction_factory(budget=budget, period=budgeting_period_factory(budget=budget, name="Other period"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"period_id": period.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(period__budget=budget, period__id=period.id)
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == predictions.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == prediction.id

    @pytest.mark.parametrize(
        "filter_value", ("Test", "TEST", "test", "name", "NAME", "Name", "Test name", "TEST NAME", "test name")
    )
    def test_get_predictions_list_filtered_by_period_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with period_name filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        period_name value.
        """
        budget = budget_factory(owner=base_user)
        period = budgeting_period_factory(budget=budget, name="Test name")
        prediction = expense_prediction_factory(budget=budget, period=period)
        expense_prediction_factory(budget=budget, period=budgeting_period_factory(budget=budget, name="Other"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"period_name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(period__budget=budget, period__name__icontains=filter_value)
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == predictions.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == prediction.id

    def test_get_predictions_list_filtered_by_category_id(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with category_id filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        category_id value.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget, name="Test name")
        prediction = expense_prediction_factory(budget=budget, category=category)
        expense_prediction_factory(budget=budget, category=expense_category_factory(budget=budget, name="Other"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"category_id": category.id})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(period__budget=budget, category__id=category.id)
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == predictions.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == prediction.id

    @pytest.mark.parametrize(
        "filter_value", ("Test", "TEST", "test", "name", "NAME", "Name", "Test name", "TEST NAME", "test name")
    )
    def test_get_predictions_list_filtered_by_category_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        expense_prediction_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two ExpensePrediction objects for single Budget.
        WHEN: The ExpensePredictionViewSet list view is called with category_name filter.
        THEN: Response must contain all ExpensePrediction existing in database assigned to Budget matching given
        category_name value.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget, name="Test name")
        prediction = expense_prediction_factory(budget=budget, category=category)
        expense_prediction_factory(budget=budget, category=expense_category_factory(budget=budget, name="Other"))
        api_client.force_authenticate(base_user)

        response = api_client.get(expense_prediction_url(budget.id), data={"category_name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpensePrediction.objects.all().count() == 2
        predictions = ExpensePrediction.objects.filter(category__budget=budget, category__name__icontains=filter_value)
        serializer = ExpensePredictionSerializer(
            predictions,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == predictions.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == prediction.id
