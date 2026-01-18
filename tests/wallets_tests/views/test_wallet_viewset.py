from decimal import Decimal
from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from app_users.serializers.user_serializer import UserSerializer
from wallets.models import Currency
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
        wallet_factory(members=[auth_user], name="Wallet 1", description="Some wallet")
        wallet_factory(
            members=[auth_user],
            name="Wallet 2",
            description="Other wallet",
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

    def test_wallet_list_balance_and_deposits_count(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Deposits and Transfers created in database for authenticated User.
        WHEN: WalletViewSet list endpoint called.
        THEN: HTTP 200. Response includes balance field for each wallet.
        """
        api_client.force_authenticate(base_user)
        wallet_1 = wallet_factory(members=[base_user])
        wallet_2 = wallet_factory(members=[base_user])
        for deposits_count, wallet in enumerate([wallet_1, wallet_2], start=1):
            for deposit_number in range(deposits_count):
                deposit = deposit_factory(wallet=wallet)
                income_factory(wallet=wallet, deposit=deposit, value=Decimal("600.00"))
                income_factory(wallet=wallet, deposit=deposit, value=Decimal("400.00"))
                expense_factory(wallet=wallet, deposit=deposit, value=Decimal("100.00"))
                expense_factory(wallet=wallet, deposit=deposit, value=Decimal("800.00"))

        response = api_client.get(WALLETS_URL, {"fields": "balance,deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        for idx, wallet_data in enumerate(response.data, start=1):
            assert "balance" in response.data[0]
            assert "deposits_count" in response.data[0]
            assert wallet_data["deposits_count"] == str(idx)
            assert wallet_data["balance"] == f"{idx}00.00"

    def test_wallet_list_includes_currency_name(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet created in database for authenticated User.
        WHEN: WalletViewSet list endpoint called.
        THEN: HTTP 200. Response includes currency_name field for each wallet.
        """
        api_client.force_authenticate(base_user)
        currency = Currency.objects.get(name="PLN")
        wallet_factory(members=[base_user], currency=currency)

        response = api_client.get(WALLETS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert "currency_name" in response.data[0]
        assert response.data[0]["currency_name"] == "PLN"

    def test_fields_param_balance(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers in database.
        WHEN: WalletViewSet called with fields=balance query parameter.
        THEN: Response includes balance field with correct calculation.
        """
        wallet_1 = wallet_factory(members=[base_user])
        wallet_2 = wallet_factory(members=[base_user])

        # Wallet 1 transfers
        income_factory(wallet=wallet_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet_1, value=Decimal("100.00"))
        expense_factory(wallet=wallet_1, value=Decimal("50.00"))

        # Wallet 2 transfers
        income_factory(wallet=wallet_2, value=Decimal("200.00"))
        income_factory(wallet=wallet_2, value=Decimal("100.00"))
        expense_factory(wallet=wallet_2, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "balance"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0].keys() == {"balance"}
        assert Decimal(response.data[0]["balance"]) == Decimal("50.00")
        assert Decimal(response.data[1]["balance"]) == Decimal("250.00")

    def test_fields_param_deposits_count(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposits in database.
        WHEN: WalletViewSet called with fields=deposits_count query parameter.
        THEN: Response includes deposits_count field with correct calculation.
        """
        wallet_1 = wallet_factory(members=[base_user])
        wallet_2 = wallet_factory(members=[base_user])

        # Wallet 1 deposits
        wallet_1_deposits = 3
        for _ in range(wallet_1_deposits):
            deposit_factory(wallet=wallet_1)

        # Wallet 2 transfers
        wallet_2_deposits = 5
        for _ in range(wallet_2_deposits):
            deposit_factory(wallet=wallet_2)

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0].keys() == {"deposits_count"}
        assert Decimal(response.data[0]["deposits_count"]) == wallet_1_deposits
        assert Decimal(response.data[1]["deposits_count"]) == wallet_2_deposits

    def test_fields_param_multiple_fields(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposits and transfers in database.
        WHEN: WalletViewSet called with fields=id,balance,deposits_count query parameter.
        THEN: Response includes all fields with correct calculation.
        """
        wallet_1 = wallet_factory(members=[base_user])
        wallet_2 = wallet_factory(members=[base_user])

        # Wallet 1
        wallet_1_deposit_1 = deposit_factory(wallet=wallet_1)
        income_factory(wallet=wallet_1, deposit=wallet_1_deposit_1, value=Decimal("200.00"))
        expense_factory(wallet=wallet_1, deposit=wallet_1_deposit_1, value=Decimal("100.00"))
        expense_factory(wallet=wallet_1, deposit=wallet_1_deposit_1, value=Decimal("50.00"))

        # Wallet 2
        wallet_2_deposit_1 = deposit_factory(wallet=wallet_2)
        wallet_2_deposit_2 = deposit_factory(wallet=wallet_2)
        income_factory(wallet=wallet_2, deposit=wallet_2_deposit_1, value=Decimal("200.00"))
        income_factory(wallet=wallet_2, deposit=wallet_2_deposit_2, value=Decimal("100.00"))
        expense_factory(wallet=wallet_2, deposit=wallet_2_deposit_2, value=Decimal("50.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "id,balance,deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
        assert response.data[0].keys() == {"id", "balance", "deposits_count"}
        assert Decimal(response.data[0]["balance"]) == Decimal("50.00")
        assert Decimal(response.data[0]["deposits_count"]) == 1
        assert Decimal(response.data[1]["balance"]) == Decimal("250.00")
        assert Decimal(response.data[1]["deposits_count"]) == 2

    def test_fields_param_no_fields_specified(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposit in database.
        WHEN: WalletViewSet called without fields query parameter.
        THEN: Response includes all default fields including balance and deposits_count.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_factory(wallet=wallet)

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        wallet_data = response.data[0]

        # Default fields should be present
        assert "id" in wallet_data
        assert "name" in wallet_data
        assert "balance" in wallet_data
        assert "deposits_count" in wallet_data
        assert wallet_data["balance"] == "0.00"
        assert wallet_data["deposits_count"] == "0"

    def test_fields_param_empty_string(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposit in database.
        WHEN: WalletViewSet called with empty fields query parameter.
        THEN: Response returns empty dicts.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_factory(wallet=wallet)

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": ""})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0] == {}

    def test_fields_param_invalid_field(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: WalletViewSet called with invalid field name in fields parameter.
        THEN: Response excludes invalid field and only includes valid requested fields.
        """
        wallet_factory(members=[base_user])

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "balance,invalid_field"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        # Only valid field should be present
        assert response.data[0].keys() == {"balance"}

    def test_fields_param_case_sensitivity(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: WalletViewSet called with fields parameter in different cases.
        THEN: Fields parameter is case-sensitive and only matches exact field names.
        """
        wallet_factory(members=[base_user])

        api_client.force_authenticate(base_user)
        # Test with uppercase (should not match)
        response = api_client.get(WALLETS_URL, {"fields": "BALANCE"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        # Should return empty dict or no balance field since case doesn't match
        assert "balance" not in response.data[0] or response.data[0] == {}

    def test_fields_param_ordering_with_balance(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with different balances.
        WHEN: WalletViewSet called with fields=balance and ordering=balance.
        THEN: Response is correctly ordered by balance.
        """
        wallet_1 = wallet_factory(members=[base_user], name="Wallet 1")
        wallet_2 = wallet_factory(members=[base_user], name="Wallet 2")
        wallet_3 = wallet_factory(members=[base_user], name="Wallet 3")

        # Create different balances
        income_factory(wallet=wallet_1, value=Decimal("50.00"))
        income_factory(wallet=wallet_2, value=Decimal("150.00"))
        income_factory(wallet=wallet_3, value=Decimal("100.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "balance", "ordering": "balance"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        # Check ascending order: 50, 100, 150
        assert Decimal(response.data[0]["balance"]) == Decimal("50.00")
        assert Decimal(response.data[1]["balance"]) == Decimal("100.00")
        assert Decimal(response.data[2]["balance"]) == Decimal("150.00")

    def test_fields_param_with_pagination(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with transfers.
        WHEN: WalletViewSet called with fields parameter and pagination.
        THEN: Paginated response includes requested fields correctly.
        """
        for i in range(5):
            wallet = wallet_factory(members=[base_user], name=f"Wallet {i}")
            income_factory(wallet=wallet, value=Decimal(f"{(i + 1) * 10}.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "balance,deposits_count", "page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert len(response.data["results"]) == 2
        assert response.data["count"] == 5

        # Check that fields are present in paginated results
        for wallet_data in response.data["results"]:
            assert "balance" in wallet_data
            assert "deposits_count" in wallet_data

    def test_fields_param_with_negative_balance(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with more expenses than income (negative balance).
        WHEN: WalletViewSet called with fields=balance.
        THEN: Response correctly handles negative balance values.
        """
        wallet = wallet_factory(members=[base_user])

        income_factory(wallet=wallet, value=Decimal("50.00"))
        expense_factory(wallet=wallet, value=Decimal("100.00"))

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "balance"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        wallet_data = response.data[0]

        # Balance should be -50
        assert Decimal(wallet_data["balance"]) == Decimal("-50.00")

    def test_fields_param_ordering_descending(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Multiple wallets with different deposit counts.
        WHEN: WalletViewSet called with fields=deposits_count and ordering=-deposits_count.
        THEN: Response is correctly ordered by deposits_count in descending order.
        """
        wallet_1 = wallet_factory(members=[base_user], name="Wallet 1")
        wallet_2 = wallet_factory(members=[base_user], name="Wallet 2")
        wallet_3 = wallet_factory(members=[base_user], name="Wallet 3")

        # Create different deposit counts
        for _ in range(2):
            deposit_factory(wallet=wallet_1)
        for _ in range(5):
            deposit_factory(wallet=wallet_2)
        for _ in range(3):
            deposit_factory(wallet=wallet_3)

        api_client.force_authenticate(base_user)
        response = api_client.get(WALLETS_URL, {"fields": "deposits_count", "ordering": "-deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 3

        # Check descending order: 5, 3, 2
        assert Decimal(response.data[0]["deposits_count"]) == 5
        assert Decimal(response.data[1]["deposits_count"]) == 3
        assert Decimal(response.data[2]["deposits_count"]) == 2


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
            "members": [base_user.id, user_factory().id],
            "currency": Currency.objects.get(name="PLN").id,
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
            elif key == "currency":
                assert wallet.currency.id == payload[key]
            else:
                assert getattr(wallet, key) == payload[key]
        serializer = WalletSerializer(wallet)
        assert response.data == serializer.data

    def test_error_no_currency(self, api_client: APIClient, base_user: User, user_factory: FactoryMetaClass):
        """
        GIVEN: Authenticated User as request.user. No currency in payload.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 400 returned. Wallet not created in database.
        """
        api_client.force_authenticate(base_user)
        payload = {
            "name": "Some Wallet",
            "description": "Some wallet",
            "members": [user_factory().id, user_factory().id],
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert response.data["detail"]["non_field_errors"][0] == "Currency is required."
        assert not Wallet.objects.filter(members=base_user).exists()

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
            "members": [user_factory().id, user_factory().id],
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Wallet.objects.filter(members=base_user).exists()

    def test_create_wallet_includes_request_user_as_member(
        self, api_client: APIClient, base_user: User, user_factory: FactoryMetaClass
    ):
        """
        GIVEN: Authenticated User as request.user. Valid payload without request user in members.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 201 returned. Request user automatically added as wallet member.
        """
        api_client.force_authenticate(base_user)
        other_user = user_factory()
        payload = {
            "name": "Wallet 1",
            "description": "Some wallet",
            "members": [other_user.id],
            "currency": Currency.objects.get(name="PLN").id,
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        wallet = Wallet.objects.get(id=response.data["id"])
        assert wallet.members.filter(id=base_user.id).exists()
        assert wallet.members.filter(id=other_user.id).exists()

    def test_create_wallet_includes_balance_and_deposits_count(self, api_client: APIClient, base_user: User):
        """
        GIVEN: Authenticated User as request.user. Valid payload.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 201 returned. Response includes balance and deposits_count fields.
        """
        api_client.force_authenticate(base_user)
        payload = {
            "name": "Wallet 1",
            "description": "Some wallet",
            "members": [base_user.id],
            "currency": Currency.objects.get(name="PLN").id,
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert "balance" in response.data
        assert "deposits_count" in response.data
        assert response.data["balance"] == "0.00"
        assert response.data["deposits_count"] == "0"

    def test_create_wallet_includes_currency_name(self, api_client: APIClient, base_user: User):
        """
        GIVEN: Authenticated User as request.user. Valid payload with currency.
        WHEN: WalletViewSet list endpoint called with POST.
        THEN: HTTP 201 returned. Response includes currency_name field.
        """
        api_client.force_authenticate(base_user)
        currency = Currency.objects.get(name="USD")
        payload = {
            "name": "Wallet 1",
            "description": "Some wallet",
            "members": [base_user.id],
            "currency": currency.id,
        }

        response = api_client.post(WALLETS_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert "currency_name" in response.data
        assert response.data["currency_name"] == "USD"


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

    def test_get_wallet_details_with_balance_and_deposits_count(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet, Deposits and Transfers created in database for authenticated User.
        WHEN: WalletViewSet detail endpoint called by authenticated User.
        THEN: HTTP 200. Response includes balance field for each wallet.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        deposit_1 = deposit_factory(wallet=wallet)
        income_factory(wallet=wallet, deposit=deposit_1, value=Decimal("600.00"))
        income_factory(wallet=wallet, deposit=deposit_1, value=Decimal("400.00"))
        expense_factory(wallet=wallet, deposit=deposit_1, value=Decimal("100.00"))
        expense_factory(wallet=wallet, deposit=deposit_1, value=Decimal("800.00"))
        deposit_2 = deposit_factory(wallet=wallet)
        income_factory(wallet=wallet, deposit=deposit_2, value=Decimal("1000.00"))
        income_factory(wallet=wallet, deposit=deposit_2, value=Decimal("500.00"))
        expense_factory(wallet=wallet, deposit=deposit_2, value=Decimal("100.00"))
        expense_factory(wallet=wallet, deposit=deposit_2, value=Decimal("800.00"))

        url = wallet_detail_url(wallet.id)

        response = api_client.get(url, {"fields": "balance,deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert "balance" in response.data
        assert "deposits_count" in response.data
        assert response.data["deposits_count"] == "2"
        assert response.data["balance"] == "700.00"

    def test_get_wallet_details_includes_currency_name(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet owned by authenticated User created in database.
        WHEN: WalletViewSet detail endpoint called by authenticated User.
        THEN: HTTP 200. Response includes currency_name field.
        """
        api_client.force_authenticate(base_user)
        currency = Currency.objects.get(name="EUR")
        wallet = wallet_factory(members=[base_user], currency=currency)
        url = wallet_detail_url(wallet.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "currency_name" in response.data
        assert response.data["currency_name"] == "EUR"

    def test_wallet_deposits_count_with_no_deposits(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet with no deposits created in database.
        WHEN: WalletViewSet detail endpoint called.
        THEN: HTTP 200 returned. Deposits count is 0.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["deposits_count"] == "0"

    def test_wallet_balance_with_no_transfers(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet with no transfers created in database.
        WHEN: WalletViewSet detail endpoint called.
        THEN: HTTP 200 returned. Balance is 0.00.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        url = wallet_detail_url(wallet.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["balance"] == "0.00"

    def test_fields_query_param(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with deposits and transfers in database.
        WHEN: WalletViewSet detail endpoint called with fields query parameter.
        THEN: Response includes requested fields with correct calculations.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_1 = deposit_factory(wallet=wallet)
        deposit_2 = deposit_factory(wallet=wallet)

        # Create transfers for wallet
        income_factory(wallet=wallet, deposit=deposit_1, value=Decimal("100.00"))
        income_factory(wallet=wallet, deposit=deposit_2, value=Decimal("50.00"))
        expense_factory(wallet=wallet, deposit=deposit_1, value=Decimal("30.00"))

        api_client.force_authenticate(base_user)
        url = wallet_detail_url(wallet.id)
        response = api_client.get(url, {"fields": "balance,deposits_count"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.keys() == {"balance", "deposits_count"}
        assert Decimal(response.data["balance"]) == Decimal("120.00")
        assert Decimal(response.data["deposits_count"]) == 2

    def test_fields_query_param_single_field(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet with transfers in database.
        WHEN: WalletViewSet detail endpoint called with fields=balance query parameter.
        THEN: Response includes only balance field.
        """
        wallet = wallet_factory(members=[base_user])
        income_factory(wallet=wallet, value=Decimal("250.00"))

        api_client.force_authenticate(base_user)
        url = wallet_detail_url(wallet.id)
        response = api_client.get(url, {"fields": "balance"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.keys() == {"balance"}
        assert Decimal(response.data["balance"]) == Decimal("250.00")

    def test_fields_query_param_id_field(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: WalletViewSet detail endpoint called with fields=id,name.
        THEN: Response includes only id and name fields.
        """
        wallet = wallet_factory(members=[base_user], name="Test Wallet")

        api_client.force_authenticate(base_user)
        url = wallet_detail_url(wallet.id)
        response = api_client.get(url, {"fields": "id,name"})

        assert response.status_code == status.HTTP_200_OK
        assert response.data.keys() == {"id", "name"}
        assert response.data["id"] == wallet.id
        assert response.data["name"] == "Test Wallet"

    def test_fields_query_param_no_fields(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet in database.
        WHEN: WalletViewSet detail endpoint called without fields query parameter.
        THEN: Response includes all default fields.
        """
        wallet = wallet_factory(members=[base_user])

        api_client.force_authenticate(base_user)
        url = wallet_detail_url(wallet.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        # Should include all default fields
        assert "id" in response.data
        assert "name" in response.data
        assert "description" in response.data
        assert "balance" in response.data
        assert "deposits_count" in response.data
        assert "currency" in response.data
        assert "currency_name" in response.data
        assert "members" in response.data


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
        [("name", "New name"), ("description", "New description")],
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
        payload = {"name": "Wallet", "description": "Some wallet", "currency": Currency.objects.get(name="PLN")}
        wallet = wallet_factory(members=[base_user], **payload)
        update_payload = {param: value}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert getattr(wallet, param) == value

    def test_wallet_update_currency(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet owner as request.user. Valid currency param in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Wallet currency updated in database.
        """
        api_client.force_authenticate(base_user)
        payload = {"name": "Wallet", "description": "Some wallet", "currency": Currency.objects.get(name="PLN")}
        wallet = wallet_factory(members=[base_user], **payload)
        update_payload = {"currency": Currency.objects.get(name="USD").id}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert wallet.currency.id == update_payload["currency"]

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
            "members": [base_user.id, user_1.id],
        }
        wallet = wallet_factory(**payload)
        update_payload = {"members": [base_user.id, user_1.id, user_2.id]}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        assert list(wallet.members.all().order_by("id").values_list("id", flat=True)) == update_payload["members"]

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
            "members": [base_user.id, user_1.id],
        }
        wallet = wallet_factory(**payload)
        update_payload = {"name": "UPDATE", "description": "Updated wallet", "members": [user_2.id]}
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
            ("currency", ""),
            ("currency", 0),
            ("currency", -1),
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
        old_payload = {"name": "Old wallet", "description": "Some wallet"}
        wallet_factory(members=[base_user], **old_payload)
        new_payload = {"name": "New wallet", "description": "Some wallet"}
        wallet = wallet_factory(members=[base_user], **new_payload)
        old_value = getattr(wallet, param)
        payload = {param: value}
        url = wallet_detail_url(wallet.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        wallet.refresh_from_db()
        assert getattr(wallet, param) == old_value

    def test_update_response_includes_currency_name(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet owner as request.user. Valid currency update in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Response includes updated currency_name field.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user], currency=Currency.objects.get(name="PLN"))
        url = wallet_detail_url(wallet.id)
        update_payload = {"currency": Currency.objects.get(name="EUR").id}

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        assert "currency_name" in response.data
        assert response.data["currency_name"] == "EUR"

    def test_error_update_currency_to_null(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet owner as request.user. Null currency value in payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 400 returned. Currency validation error returned.
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user], currency=Currency.objects.get(name="PLN"))
        url = wallet_detail_url(wallet.id)
        update_payload = {"currency": ""}

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert response.data["detail"]["non_field_errors"][0] == "Currency is required."

    def test_id_field_is_read_only(self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass):
        """
        GIVEN: Wallet owner as request.user. ID value in update payload.
        WHEN: WalletViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. ID not updated (read-only field).
        """
        api_client.force_authenticate(base_user)
        wallet = wallet_factory(members=[base_user])
        original_id = wallet.id
        url = wallet_detail_url(wallet.id)
        update_payload = {"id": 999999}

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        wallet.refresh_from_db()
        # ID should remain unchanged since it's read-only
        assert wallet.id == original_id
        assert response.data["id"] == original_id


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
