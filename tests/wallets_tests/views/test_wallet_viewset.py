"""
Tests for WalletViewSet:
* TestWalletViewSetList - GET on list view.
* TestWalletViewSetMembersList - GET on members view.
* TestWalletViewSetCreate - POST on list view.
* TestWalletViewSetDetail - GET on detail view.
* TestWalletViewSetUpdate - PATCH on detail view.
* TestWalletViewSetDelete - DELETE on detail view.
"""

from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from app_users.serializers.user_serializer import UserSerializer
from wallets.models.wallet_model import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer

WALLETS_URL = reverse("wallets:wallet-list")


def wallet_detail_url(wallet_id):
    """Creates and returns Wallet detail URL."""
    return reverse("wallets:wallet-detail", args=[wallet_id])


def wallet_members_url(wallet_id):
    """Creates and returns Wallet members URL."""
    return reverse("wallets:wallet-members", args=[wallet_id])


@pytest.mark.django_db
class TestWalletViewSetList:
    """Tests for list view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """
        GIVEN: AnonymousUser as request.user.
        WHEN: WalletViewSet list endpoint called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(WALLETS_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet list endpoint called.
        THEN: HTTP 200 returned.
        """
        jwt_access_token = get_jwt_access_token()
        response = api_client.get(WALLETS_URL, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Ten Wallet model instances created in database.
        WHEN: WalletViewSet called without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        for _ in range(10):
            wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(WALLETS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Ten WalletViewSet model instances created in database.
        WHEN: WalletViewSet called by Wallet member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        for _ in range(10):
            wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.get(WALLETS_URL, data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_retrieve_wallets_list(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Authenticated request.user.
        WHEN: WalletViewSet called.
        THEN: HTTP 200. List of User Wallets returned.
        """
        auth_user = user_factory()
        api_client.force_authenticate(auth_user)
        wallet_factory(members=[auth_user], name="Wallet 1", description="Some wallet", currency="PLN")
        wallet_factory(
            members=[auth_user],
            name="Wallet 2",
            description="Other wallet",
            currency="eur",
        )

        response = api_client.get(WALLETS_URL)

        wallets = Wallet.objects.filter(members=auth_user).order_by("id").distinct()
        serializer = WalletSerializer(wallets, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_wallets_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Two Wallets created for different Users in database.
        WHEN: WalletViewSet called by authenticated User.
        THEN: HTTP 200. List of User Wallets only returned.
        """
        auth_user = user_factory()
        wallet_factory(members=[auth_user])
        wallet_factory(members=[user_factory(), auth_user])
        wallet_factory()
        api_client.force_authenticate(auth_user)

        response = api_client.get(WALLETS_URL)

        wallets = Wallet.objects.filter(members=auth_user).order_by("id").distinct()
        serializer = WalletSerializer(wallets, many=True)
        assert Wallet.objects.all().count() == 3
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        assert len(response.data) == wallets.count() == 2


@pytest.mark.django_db
class TestWalletViewSetMembersList:
    """Tests for members list view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: AnonymousUser as request.user.
        WHEN: WalletViewSet members endpoint called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory()
        url = wallet_members_url(wallet.id)
        res = api_client.get(url)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet members endpoint called.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory()
        url = wallet_members_url(wallet.id)
        jwt_access_token = get_jwt_access_token()
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_wallet_members_list(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Two Wallets created in database - authenticated User is member of one.
        WHEN: WalletViewSet members endpoint called by authenticated User.
        THEN: HTTP 200. List of Wallets returned.
        """
        auth_user = user_factory()
        api_client.force_authenticate(auth_user)
        wallet = wallet_factory(members=[auth_user, user_factory()])
        wallet_factory()
        url = wallet_members_url(wallet.id)

        response = api_client.get(url)

        serializer = UserSerializer(wallet.members.all(), many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        for member in serializer.data:
            assert member["id"] == member.get("value")
            assert member["username"] == member.get("label")


@pytest.mark.django_db
class TestWalletViewSetCreate:
    """Tests for create view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: User):
        """
        GIVEN: AnonymousUser as request.user.
        WHEN: WalletViewSet list endpoint called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.post(WALLETS_URL, data={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - invalid data, but access granted.
        """
        jwt_access_token = get_jwt_access_token()
        response = api_client.post(WALLETS_URL, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_wallet(self, api_client: APIClient, base_user: User, user_factory: FactoryMetaClass):
        """
        GIVEN: Authenticated User as request.user. Valid payload.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 201 returned. Wallet created in database.
        """
        api_client.force_authenticate(base_user)
        payload = {
            "name": "Wallet 1",
            "description": "Some wallet",
            "currency": "PLN",
            "members": [base_user.id, user_factory().id],
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Wallet.objects.filter(members=base_user).count() == 1
        wallet = Wallet.objects.get(id=response.data["id"])
        for key in payload:
            if key == "members":
                members = getattr(wallet, key)
                assert members.count() == len(payload[key])
                for member_id in payload[key]:
                    assert members.filter(id=member_id).exists()
            else:
                assert getattr(wallet, key) == payload[key]
        serializer = WalletSerializer(wallet)
        assert response.data == serializer.data

    def test_error_name_too_long(self, api_client: APIClient, base_user: User, user_factory: FactoryMetaClass):
        """
        GIVEN: Authenticated User as request.user. Too long name in payload.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 400 returned. Wallet not created in database.
        """
        api_client.force_authenticate(base_user)
        max_length = Wallet._meta.get_field("name").max_length
        payload = {
            "name": (max_length + 1) * "a",
            "description": "Some wallet",
            "currency": "PLN",
            "members": [user_factory().id, user_factory().id],
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Wallet.objects.filter(members=base_user).exists()


@pytest.mark.django_db
class TestWalletViewSetDetail:
    """Tests for detail view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: AnonymousUser as request.user.
        WHEN: WalletViewSet detail endpoint called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_wallet_details(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet owned by authenticated User created in database.
        WHEN: WalletViewSet detail endpoint called by authenticated User.
        THEN: HTTP 200. Wallet details returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.get(url)
        serializer = WalletSerializer(wallet)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_other_user_wallet_details(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet owned by some User created in database.
        WHEN: WalletViewSet detail endpoint for another Users Wallet called by authenticated User.
        THEN: HTTP 404 returned.
        """
        user_1 = user_factory()
        user_2 = user_factory()
        wallet = wallet_factory(members=[user_1])
        api_client.force_authenticate(user_2)

        url = wallet_detail_url(wallet.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestWalletViewSetUpdate:
    """Tests for update view on WalletViewSet."""

    def test_put_not_allowed(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet owner as a request.user.
        WHEN: WalletViewSet detail endpoint called with PUT.
        THEN: Method not allowed. HTTP 405 returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.put(url, {})

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_auth_required(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: AnonymousUser as request.user. Wallet created in database.
        WHEN: WalletViewSet detail endpoint called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, data={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        "param, value",
        [("name", "New name"), ("description", "New description"), ("currency", "PLN")],
    )
    def test_wallet_update_single_field(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Wallet owner as request.user. Valid update param in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Wallet updated in database.
        """
        api_client.force_authenticate(base_user)
        payload = {"name": "Wallet", "description": "Some wallet", "currency": "eur"}
        wallet = wallet_factory(members=[base_user], **payload)
        update_payload = {param: value}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert getattr(wallet, param) == value

    def test_update_with_members(
        self,
        api_client: APIClient,
        base_user: User,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet owner as request.user. New members list as update param in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Wallet updated in database.
        """
        user_1 = user_factory()
        user_2 = user_factory()
        api_client.force_authenticate(base_user)
        payload = {
            "name": "Wallet",
            "description": "Some wallet",
            "currency": "eur",
            "members": [base_user.id, user_1.id],
        }
        wallet = wallet_factory(**payload)
        update_payload = {"members": [base_user.id, user_1.id, user_2.id]}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert list(wallet.members.all().values_list("id", flat=True)) == update_payload["members"]

    def test_wallet_update_many_fields(
        self,
        api_client: APIClient,
        base_user: User,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet owner as request.user. Valid update params in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Wallet updated in database.
        """
        user_1 = user_factory()
        user_2 = user_factory()
        api_client.force_authenticate(base_user)
        payload = {
            "name": "Wallet",
            "description": "Some wallet",
            "currency": "eur",
            "members": [base_user.id, user_1.id],
        }
        wallet = wallet_factory(**payload)
        update_payload = {"name": "UPDATE", "description": "Updated wallet", "currency": "pln", "members": [user_2.id]}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        for param, value in update_payload.items():
            if param == "members":
                assert list(wallet.members.all().values_list("id", flat=True)) == update_payload["members"]
            else:
                assert getattr(wallet, param) == value

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", (Wallet._meta.get_field("name").max_length + 1) * "A"),
            ("currency", (Wallet._meta.get_field("currency").max_length + 1) * "A"),
        ],
    )
    def test_error_on_wallet_update(
        self,
        api_client: APIClient,
        base_user: User,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Wallet owner as request.user. Invalid value as update param in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 400 returned. Wallet not updated in database.
        """
        user_factory()
        api_client.force_authenticate(base_user)
        old_payload = {"name": "Old wallet", "description": "Some wallet", "currency": "eur"}
        wallet_factory(members=[base_user], **old_payload)
        new_payload = {"name": "New wallet", "description": "Some wallet", "currency": "eur"}
        wallet = wallet_factory(members=[base_user], **new_payload)
        old_value = getattr(wallet, param)
        payload = {param: value}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet.refresh_from_db()
        assert getattr(wallet, param) == old_value


@pytest.mark.django_db
class TestWalletViewSetDelete:
    """Tests for delete view on WalletViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: AnonymousUser as request.user. Wallet created in database.
        WHEN: WalletViewSet detail endpoint called with DELETE without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: WalletViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_wallet(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet owner as request.user. Wallet created in database.
        WHEN: WalletViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned. Wallet deleted from database.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        assert Wallet.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Wallet.objects.all().exists()
