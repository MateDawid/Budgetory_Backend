import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models import Budget
from budgets.serializers.budget_serializer import BudgetSerializer

BUDGETS_URL = reverse("budgets:budget-list")


@pytest.mark.django_db
class TestBudgetFilterSetOrdering:
    """Tests for ordering with BudgetFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "name", "-id", "-name"),
    )
    def test_get_budgets_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Budget objects created in database.
        WHEN: The BudgetViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Budget existing in database sorted by given param.
        """
        for _ in range(5):
            budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(BUDGETS_URL, data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        budgets = Budget.objects.all().order_by(sort_param)
        serializer = BudgetSerializer(budgets, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(budgets) == 5
        assert response.data["results"] == serializer.data


@pytest.mark.django_db
class TestBudgetFilterSetFiltering:
    """Tests for filtering with BudgetFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some budget",
            "SOME BUDGET",
            "some budget",
            "SoMe BuDgEt",
            "Some",
            "some",
            "SOME",
            "Budget",
            "budget",
            "BUDGET",
        ),
    )
    def test_get_budgets_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two Budget objects for single Budget.
        WHEN: The BudgetViewSet list view is called with "name" filter.
        THEN: Response must contain all Budget existing in database containing given
        "name" value in name param.
        """
        matching_budget = budget_factory(members=[base_user], name="Some budget")
        budget_factory(members=[base_user], name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(BUDGETS_URL, data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Budget.objects.all().count() == 2
        budgets = Budget.objects.filter(id=matching_budget.id)
        serializer = BudgetSerializer(
            budgets,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == budgets.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_budget.id
