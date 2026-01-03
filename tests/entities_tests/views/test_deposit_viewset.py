from decimal import Decimal
from typing import Any

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from entities_tests.urls import deposit_detail_url, deposits_url
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models.choices.category_type import CategoryType
from entities.models.deposit_model import Deposit
from entities.serializers.deposit_serializer import DepositSerializer
from entities.views.deposit_viewset import calculate_deposit_balance, sum_deposit_transfers
from predictions.models import ExpensePrediction
from transfers.models import Transfer
from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestDepositViewSetList:
    """Tests for list view on DepositViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(deposits_url(wallet.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = deposits_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Deposit model instances for single Wallet created in database.
        WHEN: DepositViewSet called by Wallet member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id))

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Deposit model instances for single Wallet created in database.
        WHEN: DepositViewSet called by Wallet member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_user_not_wallet_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet list view called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        api_client.force_authenticate(other_user)

        response = api_client.get(deposits_url(wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_retrieve_deposit_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit model instances for single Wallet created in database.
        WHEN: DepositViewSet called by Wallet owner.
        THEN: Response with serialized Wallet Deposit list returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        for _ in range(2):
            deposit_factory(wallet=wallet)

        response = api_client.get(deposits_url(wallet.id))

        deposits = (
            Deposit.objects.distinct()
            .annotate(
                incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=calculate_deposit_balance())
            .filter(wallet=wallet)
        )
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data
        for deposit in serializer.data:
            incomes_sum = sum(
                Transfer.objects.filter(
                    deposit__id=deposit["id"], category__category_type=CategoryType.INCOME
                ).values_list("value", flat=True)
            )
            expenses_sum = sum(
                Transfer.objects.filter(
                    deposit__id=deposit["id"], category__category_type=CategoryType.EXPENSE
                ).values_list("value", flat=True)
            )
            assert deposit["incomes_sum"] == str(Decimal(incomes_sum).quantize(Decimal("0.00")))
            assert deposit["expenses_sum"] == str(Decimal(expenses_sum).quantize(Decimal("0.00")))
            assert deposit["balance"] == str(Decimal(incomes_sum - expenses_sum).quantize(Decimal("0.00")))

    def test_deposits_list_limited_to_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Deposit model instances for different Wallets created in database.
        WHEN: DepositViewSet called by one of Wallets owner.
        THEN: Response with serialized Deposit list (only from given Wallet) returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        deposit_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(deposits_url(wallet.id))

        deposits = Deposit.objects.filter(wallet=wallet)
        serializer = DepositSerializer(deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == deposits.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == deposit.id


@pytest.mark.django_db
class TestDepositViewSetCreate:
    """Tests for create Deposit on DepositViewSet."""

    PAYLOAD = {
        "name": "Supermarket",
        "description": "Supermarket in which I buy food.",
        "is_active": True,
    }

    def test_auth_required(self, api_client: APIClient, wallet: Wallet):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(deposits_url(wallet.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but invalid input.
        """
        wallet = wallet_factory(members=[base_user])
        url = deposits_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_wallet_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet list view called with POST by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        api_client.force_authenticate(other_user)

        response = api_client.post(deposits_url(wallet.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_create_single_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet instance created in database. Valid payload prepared for Deposit.
        WHEN: DepositViewSet called with POST by User belonging to Wallet with valid payload.
        THEN: Deposit object created in database with given payload. Initial categories for Deposit created.
        """
        wallet = wallet_factory(members=[base_user])
        period_1 = period_factory(wallet=wallet)
        period_2 = period_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        response = api_client.post(deposits_url(wallet.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Deposit.objects.filter(wallet=wallet).count() == 1
        deposit = Deposit.objects.get(id=response.data["id"])
        assert deposit.wallet == wallet
        for key in payload:
            assert getattr(deposit, key) == payload[key]
        assert deposit.is_deposit is True
        serializer = DepositSerializer(deposit)
        assert response.data == serializer.data
        for period in (period_1, period_2):
            assert ExpensePrediction.objects.filter(
                deposit=deposit,
                category=None,
                period=period,
                initial_plan=Decimal("0.00"),
                current_plan=Decimal("0.00"),
            ).exists()

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Wallet instance created in database. Payload for Deposit with field value too long.
        WHEN: DepositViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. Deposit not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = Deposit._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(deposits_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Deposit.objects.filter(wallet=wallet).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Wallet instance created in database. Valid payload for Deposit.
        WHEN: DepositViewSet called twice with POST by User belonging to Wallet with the same payload.
        THEN: Bad request HTTP 400 returned. Only one Deposit created in database.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(deposits_url(wallet.id), payload)
        response = api_client.post(deposits_url(wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "name" in response.data["detail"]
        assert response.data["detail"]["name"][0] == "Deposit with given name already exists in Wallet."
        assert Deposit.objects.filter(wallet=wallet).count() == 1


@pytest.mark.django_db
class TestDepositViewSetDetail:
    """Tests for detail view on DepositViewSet."""

    def test_auth_required(self, api_client: APIClient, deposit: Deposit):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(deposit_detail_url(deposit.wallet.id, deposit.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet detail view called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        deposit = deposit_factory(wallet=wallet)
        api_client.force_authenticate(other_user)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_deposit_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called by User belonging to Wallet.
        THEN: HTTP 200, Deposit details returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(wallet.id, deposit.id)

        response = api_client.get(url)
        serializer = DepositSerializer(deposit)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_deposit_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called without authentication.
        THEN: Unauthorized HTTP 401.
        """
        deposit = deposit_factory()
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_details_from_not_accessible_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        deposit = deposit_factory(wallet=wallet_factory())
        api_client.force_authenticate(base_user)

        url = deposit_detail_url(deposit.wallet.id, deposit.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."


@pytest.mark.django_db
class TestDepositViewSetUpdate:
    """Tests for update view on DepositViewSet."""

    PAYLOAD = {
        "name": "Supermarket",
        "description": "Supermarket in which I buy food.",
        "is_active": True,
        "is_deposit": False,
    }

    def test_auth_required(self, api_client: APIClient, deposit: Deposit):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.patch(deposit_detail_url(deposit.wallet.id, deposit.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: DepositViewSet detail view called with PATCH by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        deposit = deposit_factory(wallet=wallet)
        api_client.force_authenticate(other_user)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", "New name"),
            ("description", "New description"),
            ("is_active", not PAYLOAD["is_active"]),
            ("is_deposit", not PAYLOAD["is_deposit"]),
        ],
    )
    @pytest.mark.django_db
    def test_deposit_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called with PATCH by User belonging to Wallet.
        THEN: HTTP 200, Deposit updated.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(wallet.id, deposit.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        deposit.refresh_from_db()
        assert getattr(deposit, param) == update_payload[param]

    def test_deposit_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database. Valid payload with many params.
        WHEN: DepositViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. Deposit updated in database.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        deposit = deposit_factory(wallet=wallet, **payload)
        update_payload = {
            "name": "Some market",
            "description": "Updated supermarket description.",
            "is_active": False,
            "is_deposit": True,
        }
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        deposit.refresh_from_db()
        for param, value in update_payload.items():
            assert getattr(deposit, param) == value

    @pytest.mark.parametrize("param, value", [("name", PAYLOAD["name"])])
    def test_error_on_deposit_update(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database. Update payload with invalid value.
        WHEN: DepositViewSet detail view called with PATCH by User belonging to Wallet
        with invalid payload.
        THEN: Bad request HTTP 400, Deposit not updated.
        """
        wallet = wallet_factory(members=[base_user])
        deposit_factory(wallet=wallet, **self.PAYLOAD)
        deposit = deposit_factory(wallet=wallet)
        old_value = getattr(deposit, param)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(wallet.id, deposit.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        deposit.refresh_from_db()
        assert getattr(deposit, param) == old_value


@pytest.mark.django_db
class TestDepositViewSetDelete:
    """Tests for delete Deposit on DepositViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401.
        """
        deposit = deposit_factory()
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: DepositViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called with DELETE by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        deposit = deposit_factory(wallet=wallet_factory())
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(deposit.wallet.id, deposit.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_delete_deposit(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit instance for Wallet created in database.
        WHEN: DepositViewSet detail view called with DELETE by User belonging to Wallet.
        THEN: No content HTTP 204, Deposit deleted.
        """
        wallet = wallet_factory(members=[base_user])
        deposit = deposit_factory(wallet=wallet)
        api_client.force_authenticate(base_user)
        url = deposit_detail_url(wallet.id, deposit.id)

        assert wallet.entities.filter(is_deposit=True).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not wallet.entities.filter(is_deposit=True).exists()
