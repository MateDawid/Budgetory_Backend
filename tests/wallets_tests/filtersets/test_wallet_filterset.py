import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer

WALLETS_URL = reverse("wallets:wallet-list")


@pytest.mark.django_db
class TestWalletFilterSetOrdering:
    """Tests for ordering with WalletFilterSet."""

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "name", "-id", "-name"),
    )
    def test_get_wallets_list_sorted_by_single_param(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five Wallet objects created in database.
        WHEN: The WalletViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all Wallet existing in database sorted by given param.
        """
        for _ in range(5):
            wallet_factory(owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.get(WALLETS_URL, data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        wallets = Wallet.objects.all().order_by(sort_param)
        serializer = WalletSerializer(wallets, many=True)
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == len(wallets) == 5
        assert response.data == serializer.data


@pytest.mark.django_db
class TestWalletFilterSetFiltering:
    """Tests for filtering with WalletFilterSet."""

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some wallet",
            "SOME WALLET",
            "some wallet",
            "SoMe WaLLeT",
            "Some",
            "some",
            "SOME",
            "Wallet",
            "wallet",
            "WALLET",
        ),
    )
    def test_get_wallets_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two Wallet objects for single Wallet.
        WHEN: The WalletViewSet list view is called with "name" filter.
        THEN: Response must contain all Wallet existing in database containing given
        "name" value in name param.
        """
        matching_wallet = wallet_factory(owner=base_user, name="Some wallet")
        wallet_factory(owner=base_user, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(WALLETS_URL, data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert Wallet.objects.all().count() == 2
        wallets = Wallet.objects.filter(id=matching_wallet.id)
        serializer = WalletSerializer(
            wallets,
            many=True,
        )
        assert response.data and serializer.data
        assert len(response.data) == len(serializer.data) == wallets.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == matching_wallet.id
