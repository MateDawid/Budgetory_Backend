"""
Test file for both IncomeViewSet and TransferViewSet.
"""

import datetime
from decimal import Decimal
from typing import Any, Callable

import pytest
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from categories.models.choices.category_type import CategoryType
from transfers.models import Expense, Income
from transfers.models.transfer_model import Transfer
from transfers.serializers.expense_serializer import ExpenseSerializer
from transfers.serializers.income_serializer import IncomeSerializer
from wallets.models.wallet_model import Wallet


def expenses_list_url(wallet_id: int) -> str:
    """
    Create and return an Transfer list URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to list view.
    """
    return reverse("wallets:expense-list", args=[wallet_id])


def incomes_list_url(wallet_id: int) -> str:
    """
    Create and return an Income list URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to list view.
    """
    return reverse("wallets:income-list", args=[wallet_id])


def expense_detail_url(wallet_id: int, transfer_id: int) -> str:
    """
    Create and return an Transfer detail URL.

    Args:
        wallet_id (int): Wallet ID.
        transfer_id (int): Transfer ID.

    Returns:
        str: Relative url to detail view.
    """
    return reverse("wallets:expense-detail", args=[wallet_id, transfer_id])


def income_detail_url(wallet_id: int, transfer_id: int) -> str:
    """
    Create and return an Income detail URL.

    Args:
        wallet_id (int): Wallet ID.
        transfer_id (int): Transfer ID.

    Returns:
        str: Relative url to detail view.
    """
    return reverse("wallets:income-detail", args=[wallet_id, transfer_id])


def expense_bulk_delete_url(wallet_id: int) -> str:
    """
    Create and return an Transfer bulk delete URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to bulk delete view.
    """
    return reverse("wallets:expense-bulk-delete", args=[wallet_id])


def income_bulk_delete_url(wallet_id: int) -> str:
    """
    Create and return an Income bulk delete URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to bulk delete view.
    """
    return reverse("wallets:income-bulk-delete", args=[wallet_id])


def expense_copy_url(wallet_id: int) -> str:
    """
    Create and return an Expense copy URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to copy view.
    """
    return reverse("wallets:expense-copy", args=[wallet_id])


def income_copy_url(wallet_id: int) -> str:
    """
    Create and return an Income copy URL.

    Args:
        wallet_id (int): Wallet ID.

    Returns:
        str: Relative url to copy view.
    """
    return reverse("wallets:income-copy", args=[wallet_id])


@pytest.fixture(
    params=[pytest.param(expenses_list_url, id="ExpenseViewSet"), pytest.param(incomes_list_url, id="IncomeViewSet")]
)
def transfer_list_url(request):
    return request.param


@pytest.fixture(
    params=[pytest.param(expense_detail_url, id="ExpenseViewSet"), pytest.param(income_detail_url, id="IncomeViewSet")]
)
def transfer_detail_url(request):
    return request.param


@pytest.fixture(
    params=[pytest.param(expense_copy_url, id="ExpenseViewSet"), pytest.param(income_copy_url, id="IncomeViewSet")]
)
def transfer_copy_url(request):
    return request.param


@pytest.fixture(
    params=[
        pytest.param(expense_bulk_delete_url, id="ExpenseViewSet"),
        pytest.param(income_bulk_delete_url, id="IncomeViewSet"),
    ]
)
def transfer_bulk_delete_url(request):
    return request.param


def get_transfer_type_from_url_fixture(url_fixture: Callable):
    if url_fixture.__name__.startswith("expense"):
        return CategoryType.EXPENSE
    elif url_fixture.__name__.startswith("income"):
        return CategoryType.INCOME
    else:
        raise ValueError("Unsupported url fixture.")


@pytest.mark.django_db
class TestTransferViewSetList:
    """Tests for list view on TransferViewSet."""

    def test_auth_required(self, api_client: APIClient, wallet: Wallet, transfer_list_url: Callable):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(transfer_list_url(wallet.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass, transfer_list_url: Callable
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Ten Transfer model instances for single Wallet created in database.
        WHEN: TransferViewSet called by Wallet member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        for _ in range(10):
            transfer_factory(wallet=wallet, transfer_type=get_transfer_type_from_url_fixture(transfer_list_url))
        api_client.force_authenticate(base_user)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Ten Transfer model instances for single Wallet created in database.
        WHEN: TransferViewSet called by Wallet member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        wallet = wallet_factory(members=[base_user])
        for _ in range(10):
            transfer_factory(wallet=wallet, transfer_type=get_transfer_type_from_url_fixture(transfer_list_url))
        api_client.force_authenticate(base_user)

        response = api_client.get(transfer_list_url(wallet.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet list view called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        api_client.force_authenticate(other_user)

        response = api_client.get(transfer_list_url(wallet.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_retrieve_transfer_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Two Transfer model instances for single Wallet created in database.
        WHEN: TransferViewSet called by Wallet owner.
        THEN: Response with serialized Wallet Transfer list returned.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        for _ in range(2):
            transfer_factory(wallet=wallet, transfer_type=transfer_type)

        response = api_client.get(url)

        transfers = Transfer.objects.filter(period__wallet=wallet).order_by("id")
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfers, many=True)
        else:
            serializer = IncomeSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_transfers_list_limited_to_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Two Transfer model instances for different Wallets created in database.
        WHEN: TransferViewSet called by one of Wallets owner.
        THEN: Response with serialized Transfer list (only from given Wallet) returned.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type)
        transfer_factory(transfer_type=transfer_type)
        api_client.force_authenticate(base_user)

        response = api_client.get(url)

        transfers = Transfer.objects.filter(period__wallet=wallet)
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfers, many=True)
        else:
            serializer = IncomeSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_income_not_in_expense_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One Expense and one Income models instances for the same Wallet created in database.
        WHEN: ExpenseViewSet called by one of Wallets owner.
        THEN: Response with serialized Expense list (only from given Wallet) returned without Income.
        """
        wallet = wallet_factory(members=[base_user])
        expense_factory(wallet=wallet)
        income_transfer = income_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(expenses_list_url(wallet.id))

        expense_transfers = Expense.objects.filter(period__wallet=wallet)
        serializer = ExpenseSerializer(expense_transfers, many=True)
        assert Transfer.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == expense_transfers.count() == 1
        assert response.data == serializer.data
        assert income_transfer.id not in [transfer["id"] for transfer in response.data]

    def test_expense_not_in_income_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One Income and one Expense models instances for the same Wallet created in database.
        WHEN: IncomeViewSet called by one of Wallets owner.
        THEN: Response with serialized Income list (only from given Wallet) returned without Expense.
        """
        wallet = wallet_factory(members=[base_user])
        income_factory(wallet=wallet)
        expense_transfer = expense_factory(wallet=wallet)
        api_client.force_authenticate(base_user)

        response = api_client.get(incomes_list_url(wallet.id))

        income_transfers = Income.objects.filter(period__wallet=wallet)
        serializer = IncomeSerializer(income_transfers, many=True)
        assert Transfer.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == income_transfers.count() == 1
        assert response.data == serializer.data
        assert expense_transfer.id not in [transfer["id"] for transfer in response.data]


@pytest.mark.django_db
class TestTransferViewSetCreate:
    """Tests for create Transfer on TransferViewSet."""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_auth_required(self, api_client: APIClient, wallet: Wallet, transfer_list_url: Callable):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(transfer_list_url(wallet.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, wallet_factory: FactoryMetaClass, transfer_list_url: Callable
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet list endpoint called with GET.
        THEN: HTTP 400 returned - access granted, but data invalid.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet list view called with POST by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        api_client.force_authenticate(other_user)

        response = api_client.post(transfer_list_url(wallet.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    @pytest.mark.parametrize("value", [Decimal("0.01"), Decimal("99999999.99")])
    def test_create_single_transfer_successfully(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        value: Decimal,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Valid payload prepared for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with valid payload.
        THEN: Transfer object created in database with given payload.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        deposit = deposit_factory(wallet=wallet)
        payload["deposit"] = deposit.pk
        payload["category"] = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=transfer_type).pk
        payload["value"] = value

        response = api_client.post(url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).count() == 1
        match transfer_type:
            case CategoryType.EXPENSE:
                assert Transfer.expenses.filter(period__wallet=wallet).count() == 1
                assert Transfer.incomes.filter(period__wallet=wallet).count() == 0
            case CategoryType.INCOME:
                assert Transfer.expenses.filter(period__wallet=wallet).count() == 0
                assert Transfer.incomes.filter(period__wallet=wallet).count() == 1
        transfer = Transfer.objects.get(id=response.data["id"])
        assert transfer.period == period
        for key in payload:
            try:
                assert getattr(transfer, key) == payload[key]
            except AssertionError:
                assert getattr(getattr(transfer, key, None), "pk") == payload[key]
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfer)
        else:
            serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    def test_create_single_transfer_without_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Valid payload prepared for Transfer without 'entity' value.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with valid payload.
        THEN: Transfer object created in database with given payload and entity value None.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        deposit = deposit_factory(wallet=wallet)
        payload["deposit"] = deposit.pk
        payload["category"] = transfer_category_factory(wallet=wallet, deposit=deposit, category_type=transfer_type).pk
        payload["value"] = Decimal("0.01")

        response = api_client.post(transfer_list_url(wallet.id), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).count() == 1
        transfer = Transfer.objects.get(id=response.data["id"])
        assert transfer.period == period
        assert transfer.entity is None
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfer)
        else:
            serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    def test_create_single_transfer_without_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Valid payload prepared for Transfer without 'category' value.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with valid payload.
        THEN: Transfer object created in database with given payload and category value None.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        deposit = deposit_factory(wallet=wallet)
        payload["deposit"] = deposit.pk
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["value"] = Decimal("0.01")

        response = api_client.post(url, data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).count() == 1
        transfer = Transfer.objects.get(id=response.data["id"])
        assert transfer.period == period
        assert transfer.category is None
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfer)
        else:
            serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name"])
    def test_error_value_too_long(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        field_name: str,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Payload for Transfer with field value too long.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        api_client.force_authenticate(base_user)
        max_length = Transfer._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_lower_than_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        value: Decimal,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Payload for Transfer with "value" too low.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type).pk

        payload["value"] = value

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert response.data["detail"]["value"][0] == "Value should be higher than 0.00."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_value_higher_than_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Payload for Transfer with value too big.
        WHEN: TransferViewSet called with POST by User belonging to Wallet with invalid payload.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type).pk

        payload["value"] = Decimal("100000000.00")

        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_invalid_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Wallet instance created in database. Invalid Category in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        deposit = deposit_factory(wallet=wallet)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit.pk
        payload["category"] = transfer_category_factory(
            wallet=wallet,
            deposit=deposit,
            category_type=CategoryType.EXPENSE if transfer_type == CategoryType.INCOME else CategoryType.INCOME,
        ).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert (
            response.data["detail"]["category"][0] == f"Invalid TransferCategory for "
            f"{'Income' if transfer_type == CategoryType.INCOME else 'Expense'} provided."
        )
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_category_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: TransferCategory from outer Wallet in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(wallet=wallet_factory(), category_type=transfer_type).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "TransferCategory from different Wallet."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_period_matching_given_date_does_not_exist(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Date that does not match any Period in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert response.data["detail"]["non_field_errors"][0] == "Period matching given date does not exist."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_deposit_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Deposit from outer Wallet in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet_factory()).pk
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "deposit" in response.data["detail"]
        assert response.data["detail"]["deposit"][0] == "Deposit from different Wallet."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_entity_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Entity from outer Wallet in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet_factory()).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "entity" in response.data["detail"]
        assert response.data["detail"]["entity"][0] == "Entity from different Wallet."
        assert not Transfer.objects.filter(transfer_type=transfer_type, period__wallet=wallet).exists()

    def test_error_deposit_different_from_category_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_list_url: Callable,
    ):
        """
        GIVEN: Category Deposit different from Transfer Deposit in payload for Transfer.
        WHEN: TransferViewSet called with POST by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        url = transfer_list_url(wallet.id)
        transfer_type = get_transfer_type_from_url_fixture(transfer_list_url)
        period_factory(wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30))
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet).pk
        payload["deposit"] = deposit_factory(wallet=wallet).pk
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=deposit_factory(wallet=wallet), category_type=transfer_type
        ).pk

        api_client.post(url, payload)
        response = api_client.post(url, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Transfer Deposit and Transfer Category Deposit has to be the same."
        )
        assert not Transfer.objects.filter(period__wallet=wallet).exists()


@pytest.mark.django_db
class TestTransferViewSetDetail:
    """Tests for detail view on TransferViewSet."""

    def test_auth_required(
        self, api_client: APIClient, transfer_factory: FactoryMetaClass, transfer_detail_url: Callable
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type)
        res = api_client.get(transfer_detail_url(transfer.period.wallet.id, transfer.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type)
        url = transfer_detail_url(wallet.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet detail view called with GET by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        wallet = wallet_factory(members=[wallet_owner])
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        api_client.force_authenticate(other_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_get_transfer_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called by User belonging to Wallet.
        THEN: HTTP 200, Transfer details returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.get(url)
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfer)
        else:
            serializer = IncomeSerializer(transfer)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestTransferViewSetUpdate:
    """Tests for update view on TransferViewSet."""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_auth_required(
        self, api_client: APIClient, transfer_factory: FactoryMetaClass, transfer_detail_url: Callable
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type)
        res = api_client.patch(transfer_detail_url(transfer.period.wallet.id, transfer.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type)
        url = transfer_detail_url(wallet.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Wallet model instance in database.
        WHEN: TransferViewSet detail view called with PATCH by User not belonging to given Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet_owner = user_factory()
        other_user = user_factory()
        wallet = wallet_factory(members=[wallet_owner])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type)
        api_client.force_authenticate(other_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", "New name"),
            ("description", "New description"),
            ("value", Decimal(1000)),
            ("date", datetime.date(year=2024, month=9, day=15)),
        ],
    )
    @pytest.mark.django_db
    def test_transfer_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        param: str,
        value: Any,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH by User belonging to Wallet.
        THEN: HTTP 200, Transfer updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=payload["deposit"], category_type=transfer_type
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert transfer.period == period
        assert getattr(transfer, param) == update_payload[param]

    @pytest.mark.django_db
    def test_transfer_update_with_date_from_other_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with invalid Period.
        THEN: HTTP 400, Transfer not updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        new_period = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31)
        )
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=payload["deposit"], category_type=transfer_type
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, period=period, **payload)

        new_date = datetime.date(2024, 10, 1)
        update_payload = {"date": new_date}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert transfer.date == new_date
        assert transfer.period == new_period

    @pytest.mark.django_db
    def test_transfer_update_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with valid Entity.
        THEN: HTTP 200, Transfer updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=payload["deposit"], category_type=transfer_type
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_entity = entity_factory(wallet=wallet)
        update_payload = {"entity": new_entity.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == new_entity

    @pytest.mark.django_db
    def test_error_transfer_update_entity_with_deposit_field_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with the same Deposit in "entity" field as already
        assigned in "deposit" field.
        THEN: HTTP 400, Transfer not updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        update_payload = {"entity": payload["deposit"].pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "'deposit' and 'entity' fields cannot contain the same value."
        )
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == payload["entity"]

    @pytest.mark.django_db
    def test_error_transfer_update_entity_same_as_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with the same Deposit in "deposit" field as already
        assigned in "entity" field.
        THEN: HTTP 400, Transfer not updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = deposit_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        update_payload = {"deposit": payload["entity"].pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "'deposit' and 'entity' fields cannot contain the same value."
        )
        transfer.refresh_from_db()
        assert getattr(transfer, "deposit") == payload["deposit"]

    @pytest.mark.django_db
    def test_error_transfer_update_deposit_with_entity_instance(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with the same Entity with is_deposit=False in
        "deposit" field.
        THEN: HTTP 400, Transfer not updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_deposit = entity_factory(wallet=wallet, is_deposit=False)
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == payload["entity"]

    @pytest.mark.django_db
    def test_error_on_transfer_update_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with invalid TransferCategory.
        THEN: HTTP 200, Transfer updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet,
            category_type=CategoryType.INCOME if transfer_type == CategoryType.INCOME else CategoryType.EXPENSE,
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_category = transfer_category_factory(
            wallet=wallet,
            category_type=CategoryType.EXPENSE if transfer_type == CategoryType.INCOME else CategoryType.INCOME,
        )
        update_payload = {"category": new_category.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        transfer.refresh_from_db()
        assert getattr(transfer, "category") == payload["category"]

    def test_transfer_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PATCH with valid payload with many fields.
        THEN: HTTP 200, Transfer updated.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=payload["deposit"], category_type=transfer_type
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        update_deposit = deposit_factory(wallet=wallet)
        update_period = period_factory(
            wallet=wallet,
            date_start=datetime.date(2024, 10, 1),
            date_end=datetime.date(2024, 10, 31),
        )
        update_payload = {
            "name": "New name",
            "description": "New description",
            "value": Decimal(1000),
            "date": datetime.date(year=2024, month=10, day=1),
            "entity": entity_factory(wallet=wallet).pk,
            "deposit": update_deposit.pk,
            "category": transfer_category_factory(
                wallet=wallet, deposit=update_deposit, category_type=transfer_type
            ).pk,
        }
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert transfer.period == update_period
        for key in update_payload:
            try:
                assert getattr(transfer, key) == update_payload[key]
            except AssertionError:
                assert getattr(getattr(transfer, key, None), "pk") == update_payload[key]
        if transfer_type == CategoryType.EXPENSE:
            serializer = ExpenseSerializer(transfer)
        else:
            serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    def test_error_period_matching_given_date_does_not_exist(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Period from outer Wallet in upload payload for Transfer.
        WHEN: TransferViewSet called with PATCH by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        update_payload = {"date": datetime.date(2024, 10, 1)}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["non_field_errors"][0] == "Period matching given date does not exist."
        transfer.refresh_from_db()
        assert getattr(transfer, "date") == payload["date"]
        assert getattr(transfer, "period") == payload["period"]

    def test_error_category_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: TransferCategory from outer Wallet in upload payload for Transfer.
        WHEN: TransferViewSet called with PATCH by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_category = transfer_category_factory(wallet=wallet_factory(), category_type=transfer_type)
        update_payload = {"category": new_category.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["category"][0] == "TransferCategory from different Wallet."
        transfer.refresh_from_db()
        assert getattr(transfer, "category") == payload["category"]

    def test_error_deposit_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Deposit from outer Wallet in upload payload for Transfer.
        WHEN: TransferViewSet called with PATCH by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_deposit = deposit_factory(wallet=wallet_factory())
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["deposit"][0] == "Deposit from different Wallet."
        transfer.refresh_from_db()
        assert getattr(transfer, "deposit") == payload["deposit"]

    def test_error_entity_from_outer_wallet(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Entity from outer Wallet in upload payload for Transfer.
        WHEN: TransferViewSet called with PATCH by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not created in database.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, category_type=transfer_type)
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_entity = entity_factory(wallet=wallet_factory())
        update_payload = {"entity": new_entity.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["entity"][0] == "Entity from different Wallet."
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == payload["entity"]

    def test_error_deposit_different_from_category_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Category Deposit different from Transfer Deposit in payload for Transfer.
        WHEN: TransferViewSet called with PATCH by User belonging to Wallet.
        THEN: Bad request HTTP 400 returned. Transfer not updated in database.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(
            wallet=wallet, deposit=payload["deposit"], category_type=transfer_type
        )
        transfer = transfer_factory(wallet=wallet, transfer_type=transfer_type, **payload)
        new_deposit = deposit_factory(wallet=wallet)
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Transfer Deposit and Transfer Category Deposit has to be the same."
        )
        transfer.refresh_from_db()
        assert getattr(transfer, "deposit") == payload["deposit"]


@pytest.mark.django_db
class TestTransferViewSetDelete:
    """Tests for delete Transfer on TransferViewSet."""

    def test_auth_required(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type)
        url = transfer_detail_url(transfer.period.wallet.id, transfer.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        url = transfer_detail_url(wallet.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with DELETE by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet_factory())
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(transfer.period.wallet.id, transfer.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_delete_transfer(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_detail_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet detail view called with DELETE by User belonging to Wallet.
        THEN: No content HTTP 204, Transfer deleted.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_detail_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(wallet.id, transfer.id)

        assert Transfer.objects.filter(transfer_type=transfer_type).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Transfer.objects.filter(transfer_type=transfer_type).exists()


@pytest.mark.django_db
class TestTransferViewSetBulkDelete:
    """Tests for bulk_delete Transfer on TransferViewSet."""

    def test_auth_required(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        transfer_factory: FactoryMetaClass,
        transfer_bulk_delete_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: Transfer bulk delete view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_bulk_delete_url)
        transfer = transfer_factory(transfer_type=transfer_type)
        url = transfer_bulk_delete_url(transfer.period.wallet.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_bulk_delete_url: Callable,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet bulk delete endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_bulk_delete_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        url = transfer_bulk_delete_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(
            url, data={"objects_ids": [transfer.id]}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}", format="json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_bulk_delete_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet bulk delete view called with DELETE by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        api_client.force_authenticate(base_user)
        url = transfer_bulk_delete_url(wallet.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_bulk_delete_transfers(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_bulk_delete_url: Callable,
    ):
        """
        GIVEN: Transfer instances for Wallet created in database.
        WHEN: TransferViewSet bulk delete view called with DELETE by User belonging to Wallet.
        THEN: No content HTTP 204, Transfers deleted.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_bulk_delete_url)
        transfer_1 = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        transfer_2 = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        api_client.force_authenticate(base_user)
        url = transfer_bulk_delete_url(wallet.id)

        assert Transfer.objects.filter(transfer_type=transfer_type).count() == 2

        response = api_client.delete(url, data={"objects_ids": [transfer_1.id, transfer_2.id]}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Transfer.objects.filter(transfer_type=transfer_type).exists()

    @pytest.mark.parametrize(
        "objects_ids",
        [
            None,
            [],
            "1",
            "1,2",
            1,
        ],
    )
    def test_error_bulk_delete_transfers_with_invalid_ids(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        objects_ids: Any,
        transfer_bulk_delete_url: Callable,
    ):
        """
        GIVEN: Wallet created in database.
        WHEN: TransferViewSet bulk delete view called with DELETE by User belonging to Wallet with invalid input.
        THEN: HTTP 400, Transfers not copied.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        url = transfer_bulk_delete_url(wallet.id)

        response = api_client.delete(url, data={"objects_ids": objects_ids}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTransferViewSetCopy:
    """Tests for copy Transfer on TransferViewSet."""

    def test_auth_required(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        transfer_factory: FactoryMetaClass,
        transfer_copy_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: Transfer copy view called with POST without authentication.
        THEN: Unauthorized HTTP 401.
        """
        transfer_type = get_transfer_type_from_url_fixture(transfer_copy_url)
        transfer = transfer_factory(transfer_type=transfer_type)
        url = transfer_copy_url(transfer.period.wallet.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_copy_url: Callable,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferViewSet copy endpoint called with POST.
        THEN: HTTP 201 returned.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_copy_url)
        transfer = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        url = transfer_copy_url(wallet.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(
            url, data={"objects_ids": [transfer.id]}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}", format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED

    def test_user_not_wallet_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        wallet_factory: FactoryMetaClass,
        transfer_copy_url: Callable,
    ):
        """
        GIVEN: Transfer instance for Wallet created in database.
        WHEN: TransferViewSet copy view called with POST by User not belonging to Wallet.
        THEN: Forbidden HTTP 403 returned.
        """
        wallet = wallet_factory()
        api_client.force_authenticate(base_user)
        url = transfer_copy_url(wallet.id)

        response = api_client.post(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Wallet."

    def test_copy_transfers(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
        transfer_copy_url: Callable,
    ):
        """
        GIVEN: Transfer instances for Wallet created in database.
        WHEN: TransferViewSet copy view called with POST by User belonging to Wallet.
        THEN: No content HTTP 201, Transfers copied.
        """
        wallet = wallet_factory(members=[base_user])
        transfer_type = get_transfer_type_from_url_fixture(transfer_copy_url)
        transfer_1 = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        transfer_2 = transfer_factory(transfer_type=transfer_type, wallet=wallet)
        api_client.force_authenticate(base_user)
        url = transfer_copy_url(wallet.id)

        assert Transfer.objects.filter(transfer_type=transfer_type).count() == 2

        response = api_client.post(url, data={"objects_ids": [transfer_1.id, transfer_2.id]}, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        transfers = Transfer.objects.filter(transfer_type=transfer_type)
        assert transfers.count() == 4
        serializer = ExpenseSerializer if transfer_type == CategoryType.EXPENSE else IncomeSerializer
        unique_expenses = set(
            list(transfers.values_list(*[field_name for field_name in serializer.Meta.fields if field_name != "id"]))
        )
        assert len(unique_expenses) == 2

    @pytest.mark.parametrize(
        "objects_ids",
        [
            None,
            [],
            "1",
            "1,2",
            1,
        ],
    )
    def test_error_copy_transfers_with_invalid_ids(
        self,
        api_client: APIClient,
        base_user: Any,
        wallet_factory: FactoryMetaClass,
        objects_ids: Any,
        transfer_copy_url: Callable,
    ):
        """
        GIVEN: Wallet created in database.
        WHEN: TransferViewSet copy view called with POST by User belonging to Wallet with invalid input.
        THEN: HTTP 400, Transfers not copied.
        """
        wallet = wallet_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        url = transfer_copy_url(wallet.id)

        response = api_client.post(url, data={"objects_ids": objects_ids}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
