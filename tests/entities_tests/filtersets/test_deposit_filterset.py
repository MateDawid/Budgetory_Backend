import pytest
from django.contrib.auth.models import AbstractUser
from entities_tests.urls import deposits_url
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from entities.models import Deposit
from entities.serializers.deposit_serializer import DepositSerializer


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
            "name,id",
        ),
    )
    def test_get_sorted_deposits_list(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Three Deposit objects created in database.
        WHEN: The DepositViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Deposit existing in database sorted by given param.
        """
        member_1 = user_factory(email="bob@bob.com")
        member_2 = user_factory(email="alice@alice.com")
        budget = budget_factory(members=[member_1, member_2])
        for _ in range(3):
            deposit_factory(budget=budget)
        api_client.force_authenticate(member_1)

        response = api_client.get(deposits_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        deposits = Deposit.objects.all().order_by(*sort_param.split(","))
        serializer = DepositSerializer(deposits, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(deposits) == 3
        assert response.data["results"] == serializer.data


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
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        param: str,
        filter_value: str,
    ):
        """
        GIVEN: Two Deposit objects for single Budget.
        WHEN: The DepositViewSet list view is called with CharFilter.
        THEN: Response must contain all Deposit existing in database assigned to Budget containing given
        "name" value in name param.
        """
        budget = budget_factory(members=[base_user])
        matching_deposit = deposit_factory(budget=budget, **{param: "Some deposit"})
        deposit_factory(budget=budget, **{param: "Other one"})
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(budget.id), data={param: filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = Deposit.objects.filter(budget=budget, id=matching_deposit.id)
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == deposits.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_deposit.id

    @pytest.mark.parametrize("filter_value", (True, False))
    def test_get_deposits_list_filtered_by_is_active(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        filter_value: bool,
    ):
        """
        GIVEN: Two Deposit objects for single Budget.
        WHEN: The DepositViewSet list view is called with "is_active" filter.
        THEN: Response must contain all Deposit existing in database assigned to Budget with
        matching "is_active" value.
        """
        budget = budget_factory(members=[base_user])
        matching_deposit = deposit_factory(budget=budget, name="Some deposit", is_active=filter_value)
        deposit_factory(budget=budget, name="Other one", is_active=not filter_value)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(budget.id), data={"is_active": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Deposit.objects.all().count() == 2
        deposits = Deposit.objects.filter(budget=budget, id=matching_deposit.id)
        serializer = DepositSerializer(
            deposits,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == deposits.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_deposit.id
