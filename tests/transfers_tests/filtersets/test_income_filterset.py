from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_type import CategoryType
from transfers.models.income_model import Income
from transfers.serializers.income_serializer import IncomeSerializer


def transfers_url(budget_id):
    """Create and return an Income detail URL."""
    return reverse("budgets:income-list", args=[budget_id])


def transfer_detail_url(budget_id, transfer_id):
    """Create and return an Income detail URL."""
    return reverse("budgets:income-detail", args=[budget_id, transfer_id])


@pytest.mark.django_db
class TestIncomeFilterSetOrdering:
    """Tests for ordering with IncomeFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "name",
            "value",
            "date",
            "period",
            "entity",
            "category",
            "deposit",
            "-id",
            "-name",
            "-value",
            "-date",
            "-period",
            "-entity",
            "-category",
            "-deposit",
        ),
    )
    def test_get_transfers_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Income objects created in database.
        WHEN: The IncomeViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Income existing in database sorted by given param.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(5):
            income_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        transfers = Income.objects.all().order_by(sort_param)
        serializer = IncomeSerializer(transfers, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(transfers) == 5
        assert response.data == serializer.data


@pytest.mark.django_db
class TestIncomeFilterSetFiltering:
    """Tests for filtering with IncomeFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some transfer",
            "SOME TRANSFER",
            "some transfer",
            "SoMe TrANSfEr",
            "Some",
            "some",
            "SOME",
            "Transfer",
            "transfer",
            "TRANSFER",
        ),
    )
    def test_get_transfers_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two Income objects for single Budget.
        WHEN: The IncomeViewSet list view is called with "name" filter.
        THEN: Response must contain all Income existing in database assigned to Budget containing given
        "name" value in name param.
        """
        budget = budget_factory(members=[base_user])
        matching_transfer = income_factory(budget=budget, name="Some transfer")
        income_factory(budget=budget, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, id=matching_transfer.id)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_transfer.id

    def test_get_transfers_list_filtered_by_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Budget with different BudgetingPeriods assigned.
        WHEN: The IncomeViewSet list view is called with "period" filter.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "period" value.
        """
        budget = budget_factory(members=[base_user])
        other_period = budgeting_period_factory(budget=budget, date_start=date(2024, 9, 1), date_end=date(2024, 9, 30))
        matching_period = budgeting_period_factory(
            budget=budget, date_start=date(2024, 10, 1), date_end=date(2024, 10, 31)
        )
        income_factory(budget=budget, period=other_period)
        transfer = income_factory(budget=budget, period=matching_period)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"period": matching_period.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, period=matching_period)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Budget with different Entities assigned.
        WHEN: The IncomeViewSet list view is called with "entity" filter.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "entity" value.
        """
        budget = budget_factory(members=[base_user])
        other_entity = entity_factory(budget=budget)
        matching_entity = entity_factory(budget=budget)
        income_factory(budget=budget, entity=other_entity)
        transfer = income_factory(budget=budget, entity=matching_entity)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"entity": matching_entity.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, entity=matching_entity)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Budget with different Deposits assigned.
        WHEN: The IncomeViewSet list view is called with "deposit" filter.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "deposit" value.
        """
        budget = budget_factory(members=[base_user])
        other_deposit = deposit_factory(budget=budget)
        matching_deposit = deposit_factory(budget=budget)
        income_factory(budget=budget, deposit=other_deposit)
        transfer = income_factory(budget=budget, deposit=matching_deposit)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"deposit": matching_deposit.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, deposit=matching_deposit)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Budget with different IncomeCategories assigned.
        WHEN: The IncomeViewSet list view is called with "category" filter.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "category" value.
        """
        budget = budget_factory(members=[base_user])
        other_category = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        matching_category = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        income_factory(budget=budget, category=other_category)
        transfer = income_factory(budget=budget, category=matching_category)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"category": matching_category.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, category=matching_category)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Budget with different dates assigned.
        WHEN: The IncomeViewSet list view is called with "date" filter.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "date" value.
        """
        budget = budget_factory(members=[base_user])
        period = budgeting_period_factory(budget=budget, date_start=date(2024, 10, 1), date_end=date(2024, 10, 30))
        other_date = date(year=2024, month=10, day=11)
        matching_date = date(year=2024, month=10, day=10)

        income_factory(budget=budget, period=period, date=other_date)
        transfer = income_factory(budget=budget, period=period, date=matching_date)
        api_client.force_authenticate(base_user)

        response = api_client.get(
            transfers_url(budget.id), data={"date_after": "2024-10-01", "date_before": "2024-10-10"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__budget=budget, date=matching_date)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Three Income model objects for single Budget with different values assigned.
        WHEN: The IncomeViewSet list view is called with invalid "value" filters.
        THEN: Response contains all Incomes existing in database assigned to Budget matching given
        "value" value.
        """
        budget = budget_factory(members=[base_user])
        matching_value = Decimal("100.00")

        income_factory(budget=budget, value=Decimal("1.0"))
        income_factory(budget=budget, value=Decimal("1000.0"))
        transfer = income_factory(budget=budget, value=matching_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"value_min": 100, "value_max": 900})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 3
        transfers = Income.objects.filter(period__budget=budget, value=matching_value)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id
