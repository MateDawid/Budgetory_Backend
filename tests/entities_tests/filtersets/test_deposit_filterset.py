from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from entities_tests.urls import deposits_url
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from entities.serializers.deposit_serializer import DepositSerializer
from entities.views.deposit_viewset import get_deposit_balance, sum_deposit_transfers


@pytest.mark.django_db
class TestDepositFilterSetOrdering:
    """Tests for ordering with DepositFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        (
            "id",
            "-id",
            "name",
            "-name",
            "balance",
            "-balance",
            "name,id",
        ),
    )
    def test_get_sorted_deposits_list(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Three Deposit objects created in database.
        WHEN: The DepositViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Deposit existing in database sorted by given param.
        """
        owner = user_factory(email="bob@bob.com")
        wallet = wallet_factory(owner=owner)
        for _ in range(3):
            deposit = deposit_factory(wallet=wallet)
            category = transfer_category_factory(wallet=wallet, deposit=deposit)
            for _ in range(3):
                transfer_factory(wallet=wallet, deposit=deposit, category=category)
        api_client.force_authenticate(owner)

        response = api_client.get(
            deposits_url(wallet.id),
            data={"ordering": sort_param, "fields": f"id,{sort_param.replace('-', '')}"},  # noqa:E231
        )

        assert response.status_code == status.HTTP_200_OK

        deposits = (
            Deposit.objects.all()
            .annotate(
                deposit_incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                deposit_expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=get_deposit_balance())
            .order_by(*sort_param.split(","))
        )
        serializer = DepositSerializer(deposits, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(deposits) == 3
        assert [result["id"] for result in response.data] == [result["id"] for result in serializer.data]


@pytest.mark.django_db
class TestDepositFilterSetFiltering:
    """Tests for filtering with DepositFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some deposit",
            "SOME DEPOSIT",
            "some deposit",
            "SoMe DePoSiT",
            "Some",
            "some",
            "SOME",
            "Deposit",
            "deposit",
            "DEPOSIT",
        ),
    )
    @pytest.mark.parametrize(
        "param",
        ("name", "description"),
    )
    def test_get_deposits_list_filtered_by_char_filter(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        param: str,
        filter_value: str,
    ):
        """
        GIVEN: Two Deposit objects for single Wallet.
        WHEN: The DepositViewSet list view is called with CharFilter.
        THEN: Response must contain all Deposit existing in database assigned to Wallet containing given
        "name" value in name param.
        """
        wallet = wallet_factory(owner=base_user)
        matching_deposit = deposit_factory(wallet=wallet, **{param: "Some deposit"})
        deposit_factory(wallet=wallet, **{param: "Other one"})
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={param: filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = Deposit.objects.filter(wallet=wallet, id=matching_deposit.id)
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_deposit.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_deposits_list_filtered_by_is_active(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two Deposit objects for single Wallet.
        WHEN: The DepositViewSet list view is called with "is_active" filter.
        THEN: Response must contain all Deposit existing in database assigned to Wallet with
        matching "is_active" value.
        """
        wallet = wallet_factory(owner=base_user)
        matching_deposit = deposit_factory(wallet=wallet, name="Some deposit", is_active=filter_value)
        deposit_factory(wallet=wallet, name="Other one", is_active=not filter_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={"is_active": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = Deposit.objects.filter(wallet=wallet, id=matching_deposit.id)
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_deposit.id

    def test_get_deposits_list_filtered_by_balance(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit objects for single Wallet.
        WHEN: The DepositViewSet list view is called with balance filter.
        THEN: Response must contain all Deposit existing in database assigned to Wallet matching given
        balance.
        """
        wallet = wallet_factory(owner=base_user)
        balance = "123.45"
        target_deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=target_deposit, category_type=CategoryType.INCOME)
        transfer_factory(
            wallet=wallet, deposit=target_deposit, category=category, value=Decimal(balance).quantize(Decimal("0.00"))
        )
        other_deposit = deposit_factory(wallet=wallet)
        transfer_factory(
            wallet=wallet, deposit=other_deposit, category=category, value=Decimal("234.56").quantize(Decimal("0.00"))
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={"balance": balance, "fields": "id,balance"})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = (
            Deposit.objects.annotate(
                deposit_incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                deposit_expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=get_deposit_balance())
            .filter(balance=balance)
        )
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert [result["id"] for result in response.data] == [result["id"] for result in serializer.data]
        assert response.data[0]["id"] == target_deposit.id
        assert response.data[0]["balance"] == balance

    def test_get_deposits_list_filtered_by_balance_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit objects for single Wallet.
        WHEN: The DepositViewSet list view is called with balance_max filter.
        THEN: Response must contain all Deposit existing in database assigned to Wallet matching given
        Decimal balance_max.
        """
        wallet = wallet_factory(owner=base_user)
        balance = "123.45"
        target_deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=target_deposit, category_type=CategoryType.INCOME)
        transfer_factory(
            wallet=wallet, deposit=target_deposit, category=category, value=Decimal(balance).quantize(Decimal("0.00"))
        )
        other_deposit = deposit_factory(wallet=wallet)
        transfer_factory(
            wallet=wallet, deposit=other_deposit, category=category, value=Decimal("234.56").quantize(Decimal("0.00"))
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={"balance_max": balance, "fields": "id,balance"})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = (
            Deposit.objects.annotate(
                deposit_incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                deposit_expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=get_deposit_balance())
            .filter(balance__lte=balance)
        )
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert [result["id"] for result in response.data] == [result["id"] for result in serializer.data]
        assert response.data[0]["id"] == target_deposit.id
        assert response.data[0]["balance"] == balance

    def test_get_deposits_list_filtered_by_balance_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit objects for single Wallet.
        WHEN: The DepositViewSet list view is called with balance_min filter.
        THEN: Response must contain all Deposit existing in database assigned to Wallet matching given
        balance_min value.
        """
        wallet = wallet_factory(owner=base_user)
        balance = "234.56"
        target_deposit = deposit_factory(wallet=wallet)
        category = transfer_category_factory(wallet=wallet, deposit=target_deposit, category_type=CategoryType.INCOME)
        transfer_factory(
            wallet=wallet, deposit=target_deposit, category=category, value=Decimal(balance).quantize(Decimal("0.00"))
        )
        other_deposit = deposit_factory(wallet=wallet)
        transfer_factory(
            wallet=wallet, deposit=other_deposit, category=category, value=Decimal("123.45").quantize(Decimal("0.00"))
        )
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={"balance_min": balance, "fields": "id,balance"})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = (
            Deposit.objects.annotate(
                deposit_incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                deposit_expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=get_deposit_balance())
            .filter(balance__gte=balance)
        )
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert [result["id"] for result in response.data] == [result["id"] for result in serializer.data]
        assert response.data[0]["id"] == target_deposit.id
        assert response.data[0]["balance"] == balance
