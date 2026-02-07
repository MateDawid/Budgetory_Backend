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


def transfers_url(wallet_id):
    """Create and return an Income detail URL."""
    return reverse("wallets:income-list", args=[wallet_id])


def transfer_detail_url(wallet_id, transfer_id):
    """Create and return an Income detail URL."""
    return reverse("wallets:income-detail", args=[wallet_id, transfer_id])


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
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Income objects created in database.
        WHEN: The IncomeViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Income existing in database sorted by given param.
        """
        wallet = wallet_factory(owner=base_user)
        for _ in range(5):
            income_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        transfers = Income.objects.all().order_by(sort_param, "id")
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
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two Income objects for single Wallet.
        WHEN: The IncomeViewSet list view is called with "name" filter.
        THEN: Response must contain all Income existing in database assigned to Wallet containing given
        "name" value in name param.
        """
        wallet = wallet_factory(owner=base_user)
        matching_transfer = income_factory(wallet=wallet, name="Some transfer")
        income_factory(wallet=wallet, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, id=matching_transfer.id)
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
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Wallet with different Periods assigned.
        WHEN: The IncomeViewSet list view is called with "period" filter.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "period" value.
        """
        wallet = wallet_factory(owner=base_user)
        other_period = period_factory(wallet=wallet, date_start=date(2024, 9, 1), date_end=date(2024, 9, 30))
        matching_period = period_factory(wallet=wallet, date_start=date(2024, 10, 1), date_end=date(2024, 10, 31))
        income_factory(wallet=wallet, period=other_period)
        transfer = income_factory(wallet=wallet, period=matching_period)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"period": matching_period.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, period=matching_period)
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
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Wallet with different Entities assigned.
        WHEN: The IncomeViewSet list view is called with "entity" filter.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "entity" value.
        """
        wallet = wallet_factory(owner=base_user)
        other_entity = entity_factory(wallet=wallet)
        matching_entity = entity_factory(wallet=wallet)
        income_factory(wallet=wallet, entity=other_entity)
        transfer = income_factory(wallet=wallet, entity=matching_entity)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"entity": matching_entity.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, entity=matching_entity)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_empty_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Four different Expense model objects in database.
        WHEN: The ExpenseViewSet list view is called with "entity" filter for empty value.
        THEN: Response contains all Expenses existing in database assigned to Wallet matching given
        "entity" value.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(owner=base_user)
        other_wallet = wallet_factory()
        income_factory(wallet=other_wallet, entity=entity_factory(wallet=other_wallet))
        income_factory(wallet=other_wallet, entity=None)
        income_factory(wallet=wallet, entity=entity_factory(wallet=wallet))
        matching_transfer = income_factory(wallet=wallet, entity=None)

        response = api_client.get(transfers_url(wallet.id), data={"entity": "-1"})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 4
        transfers = Income.objects.filter(period__wallet=wallet, id=matching_transfer.id)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_transfer.id
        assert response.data[0]["entity"] is None

    def test_get_transfers_list_filtered_by_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Wallet with different Deposits assigned.
        WHEN: The IncomeViewSet list view is called with "deposit" filter.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "deposit" value.
        """
        wallet = wallet_factory(owner=base_user)
        other_deposit = deposit_factory(wallet=wallet)
        matching_deposit = deposit_factory(wallet=wallet)
        income_factory(wallet=wallet, deposit=other_deposit)
        transfer = income_factory(wallet=wallet, deposit=matching_deposit)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"deposit": matching_deposit.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, deposit=matching_deposit)
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
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Wallet with different IncomeCategories assigned.
        WHEN: The IncomeViewSet list view is called with "category" filter.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "category" value.
        """
        wallet = wallet_factory(owner=base_user)
        other_category = transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)
        matching_category = transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)
        income_factory(wallet=wallet, category=other_category)
        transfer = income_factory(wallet=wallet, category=matching_category)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"category": matching_category.id})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, category=matching_category)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_get_transfers_list_filtered_by_empty_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Four different Expense model objects in database.
        WHEN: The ExpenseViewSet list view is called with "category" filter for empty value.
        THEN: Response contains all Expenses existing in database assigned to Wallet matching given
        "category" value.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(owner=base_user)
        other_wallet = wallet_factory()
        income_factory(
            wallet=other_wallet,
            category=transfer_category_factory(category_type=CategoryType.INCOME, wallet=other_wallet),
        )
        income_factory(wallet=other_wallet, category=None)
        income_factory(
            wallet=wallet, category=transfer_category_factory(category_type=CategoryType.INCOME, wallet=wallet)
        )
        matching_transfer = income_factory(wallet=wallet, category=None)

        response = api_client.get(transfers_url(wallet.id), data={"category": "-1"})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 4
        transfers = Income.objects.filter(period__wallet=wallet, id=matching_transfer.id)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_transfer.id
        assert response.data[0]["category"] is None

    def test_get_transfers_list_filtered_by_date(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model objects for single Wallet with different dates assigned.
        WHEN: The IncomeViewSet list view is called with "date" filter.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "date" value.
        """
        wallet = wallet_factory(owner=base_user)
        period = period_factory(wallet=wallet, date_start=date(2024, 10, 1), date_end=date(2024, 10, 30))
        other_date = date(year=2024, month=10, day=11)
        matching_date = date(year=2024, month=10, day=10)

        income_factory(wallet=wallet, period=period, date=other_date)
        transfer = income_factory(wallet=wallet, period=period, date=matching_date)
        api_client.force_authenticate(base_user)

        response = api_client.get(
            transfers_url(wallet.id), data={"date_after": "2024-10-01", "date_before": "2024-10-10"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 2
        transfers = Income.objects.filter(period__wallet=wallet, date=matching_date)
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
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Three Income model objects for single Wallet with different values assigned.
        WHEN: The IncomeViewSet list view is called with invalid "value" filters.
        THEN: Response contains all Incomes existing in database assigned to Wallet matching given
        "value" value.
        """
        wallet = wallet_factory(owner=base_user)
        matching_value = Decimal("100.00")

        income_factory(wallet=wallet, value=Decimal("1.0"))
        income_factory(wallet=wallet, value=Decimal("1000.0"))
        transfer = income_factory(wallet=wallet, value=matching_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(wallet.id), data={"value_min": 100, "value_max": 900})

        assert response.status_code == status.HTTP_200_OK
        assert Income.objects.all().count() == 3
        transfers = Income.objects.filter(period__wallet=wallet, value=matching_value)
        serializer = IncomeSerializer(
            transfers,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id
