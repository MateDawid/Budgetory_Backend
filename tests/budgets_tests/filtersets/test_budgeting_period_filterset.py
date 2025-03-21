from datetime import date

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models import BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from budgets.serializers.budgeting_period_serializer import BudgetingPeriodSerializer


def periods_url(budget_id):
    """Creates and returns Budget BudgetingPeriods URL."""
    return reverse("budgets:period-list", args=[budget_id])


def period_detail_url(budget_id, period_id):
    """Creates and returns BudgetingPeriod detail URL."""
    return reverse("budgets:period-detail", args=[budget_id, period_id])


@pytest.mark.django_db
class TestBudgetingPeriodFilterSetOrdering:
    """Tests for ordering with BudgetingPeriodFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "name", "status", "-status", "date_start", "date_end", "-id", "-name", "-date_start", "-date_end"),
    )
    def test_get_periods_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five BudgetingPeriod objects created in database.
        WHEN: The BudgetingPeriodViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all BudgetingPeriod existing in database sorted by given param.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(5):
            budgeting_period_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        periods = BudgetingPeriod.objects.all().order_by(sort_param)
        serializer = BudgetingPeriodSerializer(periods, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(periods) == 5
        assert response.data["results"] == serializer.data


@pytest.mark.django_db
class TestBudgetingPeriodFilterSetFiltering:
    """Tests for filtering with BudgetingPeriodFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some period",
            "SOME PERIOD",
            "some period",
            "SoMe PeRiOd",
            "Some",
            "some",
            "SOME",
            "Period",
            "period",
            "PERIOD",
        ),
    )
    def test_get_periods_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two BudgetingPeriod objects for single Budget.
        WHEN: The BudgetingPeriodViewSet list view is called with "name" filter.
        THEN: Response must contain all BudgetingPeriod existing in database assigned to Budget containing given
        "name" value in name param.
        """
        budget = budget_factory(members=[base_user])
        matching_period = budgeting_period_factory(budget=budget, name="Some period")
        budgeting_period_factory(budget=budget, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(budget.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert BudgetingPeriod.objects.all().count() == 2
        periods = BudgetingPeriod.objects.filter(id=matching_period.id)
        serializer = BudgetingPeriodSerializer(
            periods,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == periods.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_period.id

    @pytest.mark.parametrize("date_param", ("date_start", "date_end"))
    def test_get_periods_list_filtered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        date_param: str,
    ):
        """
        GIVEN: Two BudgetingPeriod model objects for single Budget with different dates assigned.
        WHEN: The BudgetingPeriodViewSet list view is called with date filter.
        THEN: Response contains all BudgetingPeriods existing in database assigned to Budget matching given
        date value.
        """
        budget = budget_factory(members=[base_user])
        other_date_start, other_date_end = date(year=2024, month=10, day=1), date(year=2024, month=10, day=31)
        matching_date_start, matching_date_end = date(year=2024, month=11, day=1), date(year=2024, month=11, day=30)

        budgeting_period_factory(budget=budget, date_start=other_date_start, date_end=other_date_end)
        period = budgeting_period_factory(budget=budget, date_start=matching_date_start, date_end=matching_date_end)
        api_client.force_authenticate(base_user)

        payload = (
            {"date_start_after": "2024-11-01", "date_start_before": "2024-11-01"}
            if date_param == "date_start"
            else {"date_end_after": "2024-11-30", "date_end_before": "2024-11-30"}
        )
        response = api_client.get(periods_url(budget.id), data=payload)

        assert response.status_code == status.HTTP_200_OK
        assert BudgetingPeriod.objects.all().count() == 2
        periods = BudgetingPeriod.objects.filter(date_start=matching_date_start)
        serializer = BudgetingPeriodSerializer(
            periods,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == periods.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == period.id

    def test_get_periods_list_filtered_by_status(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two BudgetingPeriod objects for single Budget - one with status = PeriodStatus.ACTIVE,
        one with status = PeriodStatus.CLOSED.
        WHEN: The BudgetingPeriodViewSet list view is called with status filter.
        THEN: Response must contain all BudgetingPeriod existing in database with specified status value.
        """
        budget = budget_factory(members=[base_user])
        budgeting_period_factory(
            budget=budget,
            status=PeriodStatus.CLOSED,
            date_start=date(year=2024, month=10, day=1),
            date_end=date(year=2024, month=10, day=31),
        )
        period = budgeting_period_factory(
            budget=budget,
            status=PeriodStatus.ACTIVE,
            date_start=date(year=2024, month=11, day=1),
            date_end=date(year=2024, month=11, day=30),
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(periods_url(budget.id), data={"status": PeriodStatus.ACTIVE})

        assert response.status_code == status.HTTP_200_OK
        assert BudgetingPeriod.objects.all().count() == 2
        periods = BudgetingPeriod.objects.filter(status=PeriodStatus.ACTIVE)
        serializer = BudgetingPeriodSerializer(
            periods,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == periods.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == period.id
