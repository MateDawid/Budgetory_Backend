from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from budgets.models.budget_model import Budget
from wallets.models.wallet_model import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer


def wallets_url(budget_id):
    """Create and return an Wallet detail URL."""
    return reverse("budgets:wallet-list", args=[budget_id])


def wallet_detail_url(budget_id, wallet_id):
    """Create and return an Wallet detail URL."""
    return reverse("budgets:wallet-detail", args=[budget_id, wallet_id])


@pytest.mark.django_db
class TestWalletViewSetList:
    """Tests for list view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(wallets_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(owner=base_user)
        url = wallets_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet list view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(wallets_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_wallet_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Wallet model instances for single Budget created in database.
        WHEN: WalletViewSet called by Budget owner.
        THEN: Response with serialized Budget Wallet list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            wallet_factory(budget=budget)

        response = api_client.get(wallets_url(budget.id))

        wallets = Wallet.objects.filter(budget=budget)
        serializer = WalletSerializer(wallets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_wallets_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Wallet model instances for different Budgets created in database.
        WHEN: WalletViewSet called by one of Budgets owner.
        THEN: Response with serialized Wallet list (only from given Budget) returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        wallet_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(wallets_url(budget.id))

        wallets = Wallet.objects.filter(budget=budget)
        serializer = WalletSerializer(wallets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == wallets.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == wallet.id


@pytest.mark.django_db
class TestWalletViewSetCreate:
    """Tests for create Wallet on WalletViewSet."""

    PAYLOAD: dict = {"name": "Long term wallet"}

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(wallets_url(budget.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but data invalid.
        """
        budget = budget_factory(owner=base_user)
        url = wallets_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.post(wallets_url(budget.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_create_single_wallet(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for Wallet.
        WHEN: WalletViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Wallet object created in database with given payload
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.post(wallets_url(budget.id), self.PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert Wallet.objects.filter(budget=budget).count() == 1
        wallet = Wallet.objects.get(id=response.data["id"])
        assert wallet.budget == budget
        for key in self.PAYLOAD:
            assert getattr(wallet, key) == self.PAYLOAD[key]
        serializer = WalletSerializer(wallet)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for Wallet with field value too long.
        WHEN: WalletViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Wallet not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = Wallet._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(wallets_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Wallet.objects.filter(budget=budget).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Wallet.
        WHEN: WalletViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one Wallet created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(wallets_url(budget.id), payload)
        response = api_client.post(wallets_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == "Wallet name used already in Budget."
        assert Wallet.objects.filter(budget=budget).count() == 1


@pytest.mark.django_db
class TestWalletViewSetDetail:
    """Tests for detail view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet: Wallet):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(wallet_detail_url(wallet.budget.id, wallet.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        url = wallet_detail_url(budget.id, wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet detail view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        wallet = wallet_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = wallet_detail_url(wallet.budget.id, wallet.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_wallet_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance for Budget created in database.
        WHEN: WalletViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, Wallet details returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = wallet_detail_url(budget.id, wallet.id)

        response = api_client.get(url)
        serializer = WalletSerializer(wallet)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestWalletViewSetUpdate:
    """Tests for update view on WalletViewSet."""

    PAYLOAD = {
        "name": "Long term wallet",
    }

    def test_auth_required(self, api_client: APIClient, wallet: Wallet):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.patch(wallet_detail_url(wallet.budget.id, wallet.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        url = wallet_detail_url(budget.id, wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: WalletViewSet detail view called with PATCH by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        wallet = wallet_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = wallet_detail_url(wallet.budget.id, wallet.id)

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", "New name"),
        ],
    )
    @pytest.mark.django_db
    def test_wallet_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Wallet instance for Budget created in database.
        WHEN: WalletViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, Wallet updated.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = wallet_detail_url(budget.id, wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert getattr(wallet, param) == update_payload[param]

    @pytest.mark.parametrize("param, value", [("name", PAYLOAD["name"])])
    def test_error_on_wallet_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Wallet instance for Budget created in database. Update payload with invalid value.
        WHEN: WalletViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, Wallet not updated.
        """
        budget = budget_factory(owner=base_user)
        wallet_factory(budget=budget, **self.PAYLOAD)
        wallet = wallet_factory(budget=budget)
        old_value = getattr(wallet, param)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = wallet_detail_url(budget.id, wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet.refresh_from_db()
        assert getattr(wallet, param) == old_value


@pytest.mark.django_db
class TestWalletViewSetDelete:
    """Tests for delete Wallet on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet instance for Budget created in database.
        WHEN: WalletViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        wallet = wallet_factory()
        url = wallet_detail_url(wallet.budget.id, wallet.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        url = wallet_detail_url(budget.id, wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance for Budget created in database.
        WHEN: WalletViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)
        url = wallet_detail_url(wallet.budget.id, wallet.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_delete_wallet(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance for Budget created in database.
        WHEN: WalletViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, Wallet deleted.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = wallet_detail_url(budget.id, wallet.id)

        assert budget.wallets.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not budget.wallets.all().exists()
