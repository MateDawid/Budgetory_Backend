from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from wallets.models.wallet_deposit_model import WalletDeposit
from wallets.serializers.wallet_deposit_serializer import WalletDepositSerializer


def wallet_deposit_url(budget_id: int, wallet_id: int):
    """Create and return an WalletDeposit list URL."""
    return reverse("budgets:wallet_deposit-list", args=[budget_id, wallet_id])


def wallet_deposit_detail_url(budget_id: int, wallet_id: int, wallet_deposit_id: int):
    """Create and return an WalletDeposit detail URL."""
    return reverse("budgets:wallet_deposit-detail", args=[budget_id, wallet_id, wallet_deposit_id])


@pytest.mark.django_db
class TestWalletDepositViewSetList:
    """Tests for list view on WalletDepositViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet_deposit: WalletDeposit):
        """
        GIVEN: WalletDeposit model instance in database.
        WHEN: WalletDepositViewSet list method called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(wallet_deposit_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: WalletDeposit model instance in database.
        WHEN: WalletDepositViewSet list method called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        wallet_deposit = wallet_deposit_factory()

        api_client.force_authenticate(other_user)

        response = api_client.get(wallet_deposit_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_wallet_deposit_list_by_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two WalletDeposit model instances for single Budget created in database.
        WHEN: WalletDepositViewSet called by Budget member.
        THEN: Response with serialized Budget WalletDeposit list returned.
        """
        api_client.force_authenticate(base_user)
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        for _ in range(2):
            wallet_deposit_factory(budget=budget, wallet=wallet)

        response = api_client.get(wallet_deposit_url(budget.id, wallet.id))

        wallet_deposits = WalletDeposit.objects.filter(wallet__budget=budget)
        serializer = WalletDepositSerializer(wallet_deposits, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_wallet_deposit_list_limited_to_budget_and_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Three WalletDeposit model instances for different Budgets and Wallets created in database.
        WHEN: WalletDepositViewSet called by one of Budgets owner with Budget and Wallet ids.
        THEN: Response with serialized WalletDeposit list (only from given Budget and Wallet) returned.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        wallet_deposit = wallet_deposit_factory(budget=budget, wallet=wallet)
        # WalletDeposit from the same Budget, but different Wallet
        wallet_deposit_factory(budget=budget)
        # WalletDeposit from different Budget
        wallet_deposit_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(wallet_deposit_url(budget.id, wallet.id))

        wallet_deposits = WalletDeposit.objects.filter(wallet=wallet)
        serializer = WalletDepositSerializer(wallet_deposits, many=True)
        assert WalletDeposit.objects.all().count() == 3
        assert WalletDeposit.objects.filter(wallet__budget=budget).count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == wallet_deposits.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == wallet_deposit.id


@pytest.mark.django_db
class TestWalletDepositViewSetCreate:
    """Tests for create WalletDeposit on WalletDepositViewSet."""

    PAYLOAD = {
        "planned_weight": Decimal("60.00"),
    }

    def test_auth_required(self, api_client: APIClient, wallet_deposit: WalletDeposit):
        """
        GIVEN: WalletDeposit model instance in database.
        WHEN: WalletDepositViewSet list method called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        url = wallet_deposit_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id)
        response = api_client.post(url, data={})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget and Wallet instances created in database. Valid payload
        for WalletDeposit.
        WHEN: WalletDepositViewSet called with POST by User not belonging to Budget with valid payload.
        THEN: Forbidden HTTP 403 returned. Object not created.
        """
        wallet = wallet_factory()
        payload = self.PAYLOAD.copy()
        api_client.force_authenticate(base_user)

        response = api_client.post(wallet_deposit_url(wallet.budget.id, wallet.id), payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."
        assert not WalletDeposit.objects.filter(wallet=wallet).exists()

    def test_create_single_wallet_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget and Wallet instances created in database. Valid payload prepared
        for WalletDeposit.
        WHEN: WalletDepositViewSet called with POST by User belonging to Budget with valid payload.
        THEN: WalletDeposit object created in database with given payload
        """
        other_user = user_factory()
        budget = budget_factory(owner=base_user, members=[other_user])
        wallet = wallet_factory(budget=budget)
        deposit = deposit_factory(budget=budget)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit.id
        api_client.force_authenticate(base_user)
        url = wallet_deposit_url(budget.id, wallet.id)

        # Why planned weight is None?
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert WalletDeposit.objects.filter(wallet=wallet).count() == 1
        wallet_deposit = WalletDeposit.objects.get(id=response.data["id"])
        for key in payload:
            if key == "deposit":
                assert getattr(getattr(wallet_deposit, key), "id") == payload[key]
            else:
                assert getattr(wallet_deposit, key) == payload[key]
        assert wallet_deposit.deposit == deposit
        assert wallet_deposit.wallet == wallet
        serializer = WalletDepositSerializer(wallet_deposit)
        assert response.data == serializer.data

    def test_error_deposit_from_other_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Budgets and one Wallet in database. Payload for WalletDeposit with Deposit from Budget other
        than Wallet Budget.
        WHEN: WalletDepositViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. WalletDeposit not created in database.
        """
        user_budget = budget_factory(owner=base_user)
        other_budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=user_budget)
        deposit = deposit_factory(budget=other_budget)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit.id

        response = api_client.post(wallet_deposit_url(user_budget.id, wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert response.data["detail"]["non_field_errors"][0] == "Budget not the same for Wallet and Deposit."
        assert not WalletDeposit.objects.filter(wallet=wallet).exists()

    def test_error_second_deposit_usage(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Wallets for single Budget in database. One Wallet has Deposit already assigned in WalletDeposit.
        Payload for new WalletDeposit with Deposit already assigned to other Wallet in payload.
        WHEN: WalletDepositViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. WalletDeposit not created in database.
        """
        budget = budget_factory(owner=base_user)
        wallet_1 = wallet_factory(budget=budget)
        wallet_2 = wallet_factory(budget=budget)
        deposit = deposit_factory(budget=budget)
        wallet_deposit_factory(wallet=wallet_1, deposit=deposit)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit.id

        response = api_client.post(wallet_deposit_url(budget.id, wallet_2.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "deposit" in response.data["detail"]
        assert response.data["detail"]["deposit"][0] == "wallet deposit with this deposit already exists."
        assert not WalletDeposit.objects.filter(wallet=wallet_2).exists()

    @pytest.mark.parametrize("planned_weight", [Decimal("-0.01"), Decimal("100.01")])
    def test_error_invalid_planned_weight_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        planned_weight: Decimal,
    ):
        """
        GIVEN: Budget and Wallet instances created in database. Payload for WalletDeposit
        with field value too long.
        WHEN: WalletDepositViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. WalletDeposit not created in database.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        deposit = deposit_factory(budget=budget)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit.id
        payload["planned_weight"] = Decimal("-0.01")

        response = api_client.post(wallet_deposit_url(budget.id, wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "planned_weight" in response.data["detail"]
        assert response.data["detail"]["planned_weight"][0] == "Invalid value for planned_weight."
        assert not WalletDeposit.objects.filter(wallet__budget=budget).exists()

    def test_error_invalid_planned_weight_sum_for_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two WalletDeposits created for Wallet. Payload for third WalletDeposit with planned_weight overflowing
        acceptable Wallet planned_weight sum.
        WHEN: WalletDepositViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. WalletDeposit not created in database.
        """
        budget = budget_factory(owner=base_user)
        wallet = wallet_factory(budget=budget)
        for _ in range(2):
            wallet_deposit_factory(wallet=wallet, planned_weight=Decimal("40.00"))
        deposit = deposit_factory(budget=budget)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit.id
        payload["planned_weight"] = Decimal("20.01")

        response = api_client.post(wallet_deposit_url(budget.id, wallet.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Sum of planned weights for single Wallet cannot be greater than 100."
        )
        assert WalletDeposit.objects.filter(wallet=wallet).count() == 2


@pytest.mark.django_db
class TestWalletDepositViewSetDetail:
    """Tests for detail view on WalletDepositViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet_deposit: WalletDeposit):
        """
        GIVEN: WalletDeposit model instance in database.
        WHEN: WalletDepositViewSet detail method called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(
            wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: WalletDeposit model instance in database.
        WHEN: WalletDepositViewSet detail method called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        other_user = user_factory()
        wallet_deposit = wallet_deposit_factory()
        api_client.force_authenticate(other_user)

        response = api_client.get(
            wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize("user_type", ["owner", "member"])
    def test_get_wallet_deposit_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: WalletDeposit instance for Budget created in database.
        WHEN: WalletDepositViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, WalletDeposit details returned.
        """
        if user_type == "owner":
            budget = budget_factory(owner=base_user)
        else:
            budget = budget_factory(members=[base_user])
        wallet_deposit = wallet_deposit_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = wallet_deposit_detail_url(budget.id, wallet_deposit.wallet.id, wallet_deposit.id)

        response = api_client.get(url)
        serializer = WalletDepositSerializer(wallet_deposit)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


# @pytest.mark.django_db
# class TestWalletDepositViewSetUpdate:
#     """Tests for update view on WalletDepositViewSet."""
#
#     PAYLOAD = {
#         "value": Decimal("100.00"),
#         "description": "Expense wallet_deposit.",
#     }
#
#     def test_auth_required(
#         self, api_client: APIClient, base_user: AbstractUser, wallet_deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         wallet_deposit = wallet_deposit_factory()
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_user_not_budget_member(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with PATCH by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         wallet_deposit = wallet_deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data["detail"] == "User does not have access to Budget."
#
#     @pytest.mark.parametrize(
#         "param, value",
#         [
#             ("value", Decimal("200.00")),
#             ("description", "New description"),
#         ],
#     )
#     @pytest.mark.django_db
#     def test_wallet_deposit_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, WalletDeposit updated.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet_deposit = wallet_deposit_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(budget.id, wallet_deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         wallet_deposit.refresh_from_db()
#         assert getattr(wallet_deposit, param) == update_payload[param]
#
#     def test_wallet_deposit_update_wallet(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database. Update payload with "wallet" value prepared.
#         WHEN: WalletDepositViewSet detail view called with PATCH by User belonging to Budget with valid payload.
#         THEN: HTTP 200, Deposit updated with "wallet" value.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet = wallet_factory(budget=budget)
#         wallet_deposit = wallet_deposit_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {"wallet": wallet.id}
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(budget.id, wallet_deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         wallet_deposit.refresh_from_db()
#         assert wallet_deposit.wallet == wallet
#
#     def test_wallet_deposit_update_deposit(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database. Update payload with "deposit" value prepared.
#         WHEN: WalletDepositViewSet detail view called with PATCH by User belonging to Budget with valid payload.
#         THEN: HTTP 200, Deposit updated with "deposit" value.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget)
#         wallet_deposit = wallet_deposit_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {"deposit": deposit.id}
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(budget.id, wallet_deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         wallet_deposit.refresh_from_db()
#         assert wallet_deposit.deposit == deposit
#
#     def test_wallet_deposit_update_many_fields(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database. Valid payload with many params.
#         WHEN: WalletDepositViewSet detail endpoint called with PATCH.
#         THEN: HTTP 200 returned. WalletDeposit updated in database.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet_1 = wallet_factory(budget=budget)
#         wallet_2 = wallet_factory(budget=budget)
#         deposit_1 = deposit_factory(budget=budget)
#         deposit_2 = deposit_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         payload = {"wallet": wallet_1, "deposit": deposit_1, **self.PAYLOAD}
#         wallet_deposit = wallet_deposit_factory(budget=budget, **payload)
#         update_payload = {
#             "value": Decimal("200.00"),
#             "description": "Updated wallet_deposit.",
#             "wallet": wallet_2.id,
#             "deposit": deposit_2.id,
#         }
#         url = wallet_deposit_detail_url(budget.id, wallet_deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         wallet_deposit.refresh_from_db()
#         for param, value in update_payload.items():
#             if param in ("wallet", "deposit"):
#                 assert getattr(wallet_deposit, param).id == value
#             else:
#                 assert getattr(wallet_deposit, param) == value
#
#     def test_error_update_wallet_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. User not belonging to Budget as
#         'wallet' in payload.
#         WHEN: WalletDepositViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. WalletDeposit not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet_deposit = wallet_deposit_factory(budget=budget)
#         payload = {"wallet": wallet_factory().id}
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "non_field_errors" in response.data["detail"]
#         assert (
#             response.data["detail"]["non_field_errors"][0] == "Budget for wallet and deposit fields is not the same."
#         )
#
#     def test_error_update_deposit_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget instance created in database. User not belonging to Budget as
#         'deposit' in payload.
#         WHEN: WalletDepositViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. WalletDeposit not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet_deposit = wallet_deposit_factory(budget=budget)
#         payload = {"deposit": deposit_factory().id}
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert "non_field_errors" in response.data["detail"]
#         assert (
#             response.data["detail"]["non_field_errors"][0] == "Budget for wallet and deposit fields is not the same."
#         )
#
#
# @pytest.mark.django_db
# class TestWalletDepositViewSetDelete:
#     """Tests for delete WalletDeposit on WalletDepositViewSet."""
#
#     def test_auth_required(
#         self, api_client: APIClient, base_user: AbstractUser, wallet_deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with DELETE without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         wallet_deposit = wallet_deposit_factory()
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_user_not_budget_member(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         wallet_deposit = wallet_deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(wallet_deposit.wallet.budget.id, wallet_deposit.wallet.id, wallet_deposit.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data["detail"] == "User does not have access to Budget."
#
#     def test_delete_wallet_deposit(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         wallet_deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: WalletDeposit instance for Budget created in database.
#         WHEN: WalletDepositViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, WalletDeposit deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         wallet_deposit = wallet_deposit_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = wallet_deposit_detail_url(budget.id, wallet_deposit.id)
#
#         assert WalletDeposit.objects.filter(wallet__budget=budget).count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not WalletDeposit.objects.filter(wallet__budget=budget).exists()
