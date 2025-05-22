import datetime
from decimal import Decimal
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
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.models.income_model import Income
from transfers.models.transfer_model import Transfer
from transfers.serializers.income_serializer import IncomeSerializer


def transfers_url(budget_id: int) -> str:
    """
    Create and return an Income list URL.

    Args:
        budget_id (int): Budget ID.

    Returns:
        str: Relative url to list view.
    """
    return reverse("budgets:income-list", args=[budget_id])


def transfer_detail_url(budget_id: int, transfer_id: int) -> str:
    """
    Create and return an Income detail URL.

    Args:
        budget_id (int): Budget ID.
        transfer_id (int): Transfer ID.

    Returns:
        str: Relative url to detail view.
    """
    return reverse("budgets:income-detail", args=[budget_id, transfer_id])


def transfer_bulk_delete_url(budget_id: int) -> str:
    """
    Create and return an Income bulk delete URL.

    Args:
        budget_id (int): Budget ID.

    Returns:
        str: Relative url to detail view.
    """
    return reverse("budgets:income-bulk-delete", args=[budget_id])


@pytest.mark.django_db
class TestIncomeViewSetList:
    """Tests for list view on IncomeViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(transfers_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = transfers_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Income model instances for single Budget created in database.
        WHEN: IncomeViewSet called by Budget member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(10):
            income_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten Income model instances for single Budget created in database.
        WHEN: IncomeViewSet called by Budget member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(10):
            income_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet list view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        api_client.force_authenticate(other_user)

        response = api_client.get(transfers_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_transfer_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model instances for single Budget created in database.
        WHEN: IncomeViewSet called by Budget owner.
        THEN: Response with serialized Budget Income list returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        for _ in range(2):
            income_factory(budget=budget)

        response = api_client.get(transfers_url(budget.id))

        transfers = Income.objects.filter(period__budget=budget)
        serializer = IncomeSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_transfers_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Income model instances for different Budgets created in database.
        WHEN: IncomeViewSet called by one of Budgets owner.
        THEN: Response with serialized Income list (only from given Budget) returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        income_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id))

        transfers = Income.objects.filter(period__budget=budget)
        serializer = IncomeSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == transfers.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == transfer.id

    def test_expense_not_in_income_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One Income and one Expense models instances for the same Budget created in database.
        WHEN: IncomeViewSet called by one of Budgets owner.
        THEN: Response with serialized Income list (only from given Budget) returned without Expense.
        """
        budget = budget_factory(members=[base_user])
        income_factory(budget=budget)
        expense_transfer = expense_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id))

        income_transfers = Income.objects.filter(period__budget=budget)
        serializer = IncomeSerializer(income_transfers, many=True)
        assert Transfer.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == income_transfers.count() == 1
        assert response.data == serializer.data
        assert expense_transfer.id not in [transfer["id"] for transfer in response.data]


@pytest.mark.django_db
class TestIncomeViewSetCreate:
    """Tests for create Income on IncomeViewSet."""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(transfers_url(budget.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet list endpoint called with GET.
        THEN: HTTP 400 returned - access granted, but data invalid.
        """
        budget = budget_factory(members=[base_user])
        url = transfers_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        api_client.force_authenticate(other_user)

        response = api_client.post(transfers_url(budget.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize("value", [Decimal("0.01"), Decimal("99999999.99")])
    def test_create_single_transfer_successfully(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        value: Decimal,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Income object created in database with given payload.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR).pk
        payload["value"] = value

        response = api_client.post(transfers_url(budget.id), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Income.objects.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 0
        transfer = Income.objects.get(id=response.data["id"])
        for key in payload:
            try:
                assert getattr(transfer, key) == payload[key]
            except AssertionError:
                assert getattr(getattr(transfer, key, None), "pk") == payload[key]
        serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for Income with field value too long.
        WHEN: IncomeViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = Income._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Income.objects.filter(period__budget=budget).exists()

    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_lower_than_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        value: Decimal,
    ):
        """
        GIVEN: Budget instance created in database. Payload for Income with "value" too low.
        WHEN: IncomeViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR).pk

        payload["value"] = value

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert response.data["detail"]["value"][0] == "Value should be higher than 0.00."
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_value_higher_than_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. Payload for Income with value too big.
        WHEN: IncomeViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR).pk

        payload["value"] = Decimal("100000000.00")

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_invalid_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. IncomeCategory in payload for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Invalid TransferCategory for Income provided."
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_category_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: IncomeCategory from outer Budget in payload for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget_factory(), category_type=CategoryType.INCOME).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "TransferCategory from different Budget."
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_period_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod from outer Budget in payload for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget_factory(),
            date_start=datetime.date(2024, 9, 1),
            date_end=datetime.date(2024, 9, 30),
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "period" in response.data["detail"]
        assert response.data["detail"]["period"][0] == "BudgetingPeriod from different Budget."
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_deposit_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit from outer Budget in payload for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget_factory()).pk
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "deposit" in response.data["detail"]
        assert response.data["detail"]["deposit"][0] == "Deposit from different Budget."
        assert not Income.objects.filter(period__budget=budget).exists()

    def test_error_entity_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Entity from outer Budget in payload for Income.
        WHEN: IncomeViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        ).pk
        payload["entity"] = entity_factory(budget=budget_factory()).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "entity" in response.data["detail"]
        assert response.data["detail"]["entity"][0] == "Entity from different Budget."
        assert not Income.objects.filter(period__budget=budget).exists()


@pytest.mark.django_db
class TestIncomeViewSetDetail:
    """Tests for detail view on IncomeViewSet."""

    def test_auth_required(self, api_client: APIClient, income_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        transfer = income_factory()
        res = api_client.get(transfer_detail_url(transfer.period.budget.id, transfer.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, income_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        url = transfer_detail_url(budget.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet detail view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        transfer = income_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_transfer_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, Income details returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.get(url)
        serializer = IncomeSerializer(transfer)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestIncomeViewSetUpdate:
    """Tests for update view on IncomeViewSet."""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_auth_required(self, api_client: APIClient, income_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        transfer = income_factory()
        res = api_client.patch(transfer_detail_url(transfer.period.budget.id, transfer.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, income_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        url = transfer_detail_url(budget.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeViewSet detail view called with PATCH by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        transfer = income_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

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
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, param) == update_payload[param]

    @pytest.mark.django_db
    def test_transfer_update_both_date_and_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with invalid BudgetingPeriod.
        THEN: HTTP 400, Income not updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_period = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31)
        )
        new_date = datetime.date(2024, 10, 1)
        update_payload = {"period": new_period.pk, "date": new_date}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, "date") == new_date
        assert getattr(transfer, "period") == new_period

    @pytest.mark.django_db
    def test_error_transfer_update_period(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with valid BudgetingPeriod and date.
        THEN: HTTP 400, Income not updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_period = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31)
        )
        update_payload = {"period": new_period.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        transfer.refresh_from_db()
        assert getattr(transfer, "period") == payload["period"]

    @pytest.mark.django_db
    def test_transfer_update_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with valid Deposit.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_deposit = deposit_factory(budget=budget)
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, "deposit") == new_deposit

    @pytest.mark.django_db
    def test_transfer_update_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with valid Entity.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_entity = entity_factory(budget=budget)
        update_payload = {"entity": new_entity.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == new_entity

    @pytest.mark.django_db
    def test_error_transfer_update_entity_with_deposit_field_value(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with the same Deposit in "entity" field as already
        assigned in "deposit" field.
        THEN: HTTP 400, Income not updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        update_payload = {"entity": payload["deposit"].pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

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
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with the same Deposit in "deposit" field as already
        assigned in "entity" field.
        THEN: HTTP 400, Income not updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = deposit_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        update_payload = {"deposit": payload["entity"].pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

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
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with the same Entity with is_deposit=False in
        "deposit" field.
        THEN: HTTP 400, Income not updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_deposit = entity_factory(budget=budget, is_deposit=False)
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == payload["entity"]

    @pytest.mark.django_db
    def test_transfer_update_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with valid TransferCategory.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        new_category = transfer_category_factory(budget=budget, priority=CategoryPriority.IRREGULAR)
        update_payload = {"category": new_category.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        assert getattr(transfer, "category") == new_category

    @pytest.mark.django_db
    def test_error_on_transfer_update_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with invalid TransferCategory.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        transfer = income_factory(budget=budget, **payload)
        new_category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        update_payload = {"category": new_category.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        transfer.refresh_from_db()
        assert getattr(transfer, "category") == payload["category"]

    def test_transfer_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PATCH with valid payload with many fields.
        THEN: HTTP 200, Income updated.
        """
        budget = budget_factory(members=[base_user])
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        transfer = income_factory(budget=budget, **payload)
        update_payload = {
            "name": "New name",
            "description": "New description",
            "value": Decimal(1000),
            "date": datetime.date(year=2024, month=10, day=1),
            "period": budgeting_period_factory(
                budget=budget,
                date_start=datetime.date(2024, 10, 1),
                date_end=datetime.date(2024, 10, 31),
            ).pk,
            "entity": entity_factory(budget=budget).pk,
            "deposit": deposit_factory(budget=budget).pk,
            "category": transfer_category_factory(budget=budget, priority=CategoryPriority.IRREGULAR).pk,
        }
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        transfer.refresh_from_db()
        for key in update_payload:
            try:
                assert getattr(transfer, key) == update_payload[key]
            except AssertionError:
                assert getattr(getattr(transfer, key, None), "pk") == update_payload[key]
        serializer = IncomeSerializer(transfer)
        assert response.data == serializer.data

    def test_error_period_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod from outer Budget in upload payload for Income.
        WHEN: IncomeViewSet called with PATCH by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        transfer = income_factory(budget=budget, **payload)
        new_period = budgeting_period_factory(budget=budget_factory())
        update_payload = {"period": new_period.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["period"][0] == "BudgetingPeriod from different Budget."
        transfer.refresh_from_db()
        assert getattr(transfer, "period") == payload["period"]

    def test_error_category_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory from outer Budget in upload payload for Income.
        WHEN: IncomeViewSet called with PATCH by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        transfer = income_factory(budget=budget, **payload)
        new_category = transfer_category_factory(budget=budget_factory(), category_type=CategoryType.INCOME)
        update_payload = {"category": new_category.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["category"][0] == "TransferCategory from different Budget."
        transfer.refresh_from_db()
        assert getattr(transfer, "category") == payload["category"]

    def test_error_deposit_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit from outer Budget in upload payload for Income.
        WHEN: IncomeViewSet called with PATCH by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        transfer = income_factory(budget=budget, **payload)
        new_deposit = deposit_factory(budget=budget_factory())
        update_payload = {"deposit": new_deposit.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["deposit"][0] == "Deposit from different Budget."
        transfer.refresh_from_db()
        assert getattr(transfer, "deposit") == payload["deposit"]

    def test_error_entity_from_outer_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Entity from outer Budget in upload payload for Income.
        WHEN: IncomeViewSet called with PATCH by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Income not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        transfer = income_factory(budget=budget, **payload)
        new_entity = entity_factory(budget=budget_factory())
        update_payload = {"entity": new_entity.pk}
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["detail"]["entity"][0] == "Entity from different Budget."
        transfer.refresh_from_db()
        assert getattr(transfer, "entity") == payload["entity"]


@pytest.mark.django_db
class TestIncomeViewSetDelete:
    """Tests for delete Income on IncomeViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: AbstractUser, income_factory: FactoryMetaClass):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        transfer = income_factory()
        url = transfer_detail_url(transfer.period.budget.id, transfer.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, income_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        url = transfer_detail_url(budget.id, transfer.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        transfer = income_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(transfer.period.budget.id, transfer.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_delete_transfer(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, Income deleted.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = transfer_detail_url(budget.id, transfer.id)

        assert Income.objects.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Income.objects.all().exists()


@pytest.mark.django_db
class TestIncomeViewSetBulkDelete:
    """Tests for bulk_delete Income on IncomeViewSet."""

    def test_auth_required(self, api_client: APIClient, base_user: AbstractUser, income_factory: FactoryMetaClass):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet bulk delete view called with DELETE without authentication.
        THEN: Unauthorized HTTP 401.
        """
        transfer = income_factory()
        url = transfer_bulk_delete_url(transfer.period.budget.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self, api_client: APIClient, base_user: User, budget_factory: FactoryMetaClass, income_factory: FactoryMetaClass
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(members=[base_user])
        transfer = income_factory(budget=budget)
        url = transfer_bulk_delete_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(
            url, data={"objects_ids": [transfer.id]}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}", format="json"
        )
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)
        url = transfer_bulk_delete_url(budget.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_bulk_delete_transfers(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Income instance for Budget created in database.
        WHEN: IncomeViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, Income deleted.
        """
        budget = budget_factory(members=[base_user])
        transfer_1 = income_factory(budget=budget)
        transfer_2 = income_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = transfer_bulk_delete_url(budget.id)

        assert Income.objects.all().count() == 2

        response = api_client.delete(url, data={"objects_ids": [transfer_1.id, transfer_2.id]}, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Income.objects.all().exists()
