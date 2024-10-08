import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models.budget_model import Budget
from categories.models.transfer_category_choices import ExpenseCategoryPriority, IncomeCategoryPriority
from transfers.models.expense_model import Expense
from transfers.models.transfer_model import Transfer
from transfers.serializers.expense_serializer import ExpenseSerializer


def transfers_url(budget_id):
    """Create and return an Expense detail URL."""
    return reverse("budgets:expense-list", args=[budget_id])


def transfer_detail_url(budget_id, transfer_id):
    """Create and return an Expense detail URL."""
    return reverse("budgets:expense-detail", args=[budget_id, transfer_id])


@pytest.mark.django_db
class TestExpenseViewSetList:
    """Tests for list view on ExpenseViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(transfers_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseViewSet list view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(transfers_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_transfer_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Expense model instances for single Budget created in database.
        WHEN: ExpenseViewSet called by Budget owner.
        THEN: Response with serialized Budget Expense list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            expense_factory(budget=budget)

        response = api_client.get(transfers_url(budget.id))

        transfers = Expense.objects.filter(period__budget=budget)
        serializer = ExpenseSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_transfers_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Expense model instances for different Budgets created in database.
        WHEN: ExpenseViewSet called by one of Budgets owner.
        THEN: Response with serialized Expense list (only from given Budget) returned.
        """
        budget = budget_factory(owner=base_user)
        transfer = expense_factory(budget=budget)
        expense_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id))

        transfers = Expense.objects.filter(period__budget=budget)
        serializer = ExpenseSerializer(transfers, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == transfers.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == transfer.id

    def test_income_not_in_expense_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_factory: FactoryMetaClass,
        income_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One Expense and one Income models instances for the same Budget created in database.
        WHEN: ExpenseViewSet called by one of Budgets owner.
        THEN: Response with serialized Expense list (only from given Budget) returned without Income.
        """
        budget = budget_factory(owner=base_user)
        expense_factory(budget=budget)
        income_transfer = income_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(transfers_url(budget.id))

        expense_transfers = Expense.objects.filter(period__budget=budget)
        serializer = ExpenseSerializer(expense_transfers, many=True)
        assert Transfer.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == expense_transfers.count() == 1
        assert response.data["results"] == serializer.data
        assert income_transfer.id not in [transfer["id"] for transfer in response.data["results"]]


@pytest.mark.django_db
class TestExpenseViewSetCreate:
    """Tests for create Expense on ExpenseViewSet."""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(transfers_url(budget.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
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
        expense_category_factory: FactoryMetaClass,
        value: Decimal,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for Expense.
        WHEN: ExpenseViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Expense object created in database with given payload.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = expense_category_factory(
            budget=budget, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        ).pk
        payload["value"] = value

        response = api_client.post(transfers_url(budget.id), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 0
        transfer = Expense.objects.get(id=response.data["id"])
        for key in payload:
            try:
                assert getattr(transfer, key) == payload[key]
            except AssertionError:
                assert getattr(getattr(transfer, key, None), "pk") == payload[key]
        serializer = ExpenseSerializer(transfer)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for Expense with field value too long.
        WHEN: ExpenseViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Expense not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = Expense._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not Expense.objects.filter(period__budget=budget).exists()

    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_lower_than_min(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        value: Decimal,
    ):
        """
        GIVEN: Budget instance created in database. Payload for Expense with "value" too low.
        WHEN: ExpenseViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Expense not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = expense_category_factory(
            budget=budget, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        ).pk

        payload["value"] = value

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert response.data["detail"]["value"][0] == "Value should be higher than 0.00."
        assert not Expense.objects.filter(period__budget=budget).exists()

    def test_error_value_higher_than_max(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. Payload for Expense with value too big.
        WHEN: ExpenseViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Expense not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = expense_category_factory(
            budget=budget, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        ).pk

        payload["value"] = Decimal("100000000.00")

        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "value" in response.data["detail"]
        assert not Expense.objects.filter(period__budget=budget).exists()

    def test_error_invalid_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. IncomeCategory in payload for Expense.
        WHEN: ExpenseViewSet called with POST by User belonging to Budget.
        THEN: Bad request HTTP 400 returned. Expense not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        ).pk
        payload["entity"] = entity_factory(budget=budget).pk
        payload["deposit"] = deposit_factory(budget=budget).pk
        payload["category"] = income_category_factory(budget=budget, priority=IncomeCategoryPriority.REGULAR).pk

        api_client.post(transfers_url(budget.id), payload)
        response = api_client.post(transfers_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "category" in response.data["detail"]
        assert response.data["detail"]["category"][0] == "Invalid TransferCategory for Expense provided."
        assert not Expense.objects.filter(period__budget=budget).exists()


# @pytest.mark.django_db
# class TestExpenseViewSetDetail:
#     """Tests for detail view on ExpenseViewSet."""
#
#     def test_auth_required(self, api_client: APIClient, expense_factory: FactoryMetaClass):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: ExpenseViewSet detail view called with GET without authentication.
#         THEN: Unauthorized HTTP 401 returned.
#         """
#         transfer = expense_factory()
#         res = api_client.get(transfer_detail_url(transfer.budget.id, transfer.id))
#
#         assert res.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_user_not_budget_member(
#         self,
#         api_client: APIClient,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: ExpenseViewSet detail view called with GET by User not belonging to given Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         budget_owner = user_factory()
#         other_user = user_factory()
#         budget = budget_factory(owner=budget_owner)
#         transfer = expense_factory(budget=budget)
#         api_client.force_authenticate(other_user)
#         url = transfer_detail_url(transfer.budget.id, transfer.id)
#
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data["detail"] == "User does not have access to Budget."
#
#     def test_get_transfer_details(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database.
#         WHEN: ExpenseViewSet detail view called by User belonging to Budget.
#         THEN: HTTP 200, Expense details returned.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer = expense_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer.id)
#
#         response = api_client.get(url)
#         serializer = ExpenseSerializer(transfer)
#
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data == serializer.data
#
#
# @pytest.mark.django_db
# class TestExpenseViewSetUpdate:
#     """Tests for update view on ExpenseViewSet."""
#
#     PAYLOAD: dict[str, Any] = {
#         "name": "Bills",
#         "description": "Expenses for bills.",
#         "is_active": True,
#         "priority": ExpensePriority.MOST_IMPORTANT,
#     }
#
#     def test_auth_required(self, api_client: APIClient, expense_factory: FactoryMetaClass):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: ExpenseViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401 returned.
#         """
#         transfer = expense_factory()
#         res = api_client.patch(transfer_detail_url(transfer.budget.id, transfer.id), data={})
#
#         assert res.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_user_not_budget_member(
#         self,
#         api_client: APIClient,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget model instance in database.
#         WHEN: ExpenseViewSet detail view called with PATCH by User not belonging to given Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         budget_owner = user_factory()
#         other_user = user_factory()
#         budget = budget_factory(owner=budget_owner)
#         transfer = expense_factory(budget=budget)
#         api_client.force_authenticate(other_user)
#         url = transfer_detail_url(transfer.budget.id, transfer.id)
#
#         response = api_client.patch(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data["detail"] == "User does not have access to Budget."
#
#     @pytest.mark.parametrize(
#         "param, value",
#         [
#             ("name", "New name"),
#             ("description", "New description"),
#             ("is_active", not PAYLOAD["is_active"]),
#             ("priority", ExpensePriority.DEBTS),
#         ],
#     )
#     @pytest.mark.django_db
#     def test_transfer_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database.
#         WHEN: ExpenseViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, Expense updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer = expense_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         transfer.refresh_from_db()
#         assert getattr(transfer, param) == update_payload[param]
#
#     def test_error_on_transfer_name_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense instances for Budget created in database. Update payload with invalid "name" value.
#         WHEN: ExpenseViewSet detail view called with PATCH by User belonging to Budget
#         with invalid payload.
#         THEN: Bad request HTTP 400, Expense not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_1 = expense_factory(budget=budget, **self.PAYLOAD, owner=None)
#         transfer_2 = expense_factory(budget=budget, owner=None)
#         old_value = getattr(transfer_2, "name")
#         update_payload = {"name": transfer_1.name}
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer_2.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         transfer_2.refresh_from_db()
#         assert getattr(transfer_2, "name") == old_value
#
#     def test_error_on_transfer_priority_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense instances for Budget created in database. Update payload with invalid "priority"
#         value.
#         WHEN: ExpenseViewSet detail view called with PATCH by User belonging to Budget
#         with invalid payload.
#         THEN: Bad request HTTP 400, Expense not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer = expense_factory(budget=budget, owner=None)
#         old_value = getattr(transfer, "priority")
#         update_payload = {"priority": ExpensePriority.values[-1] + 1}
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         transfer.refresh_from_db()
#         assert getattr(transfer, "priority") == old_value
#
#     def test_error_on_transfer_owner_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two Expense instances for Budget created in database with the same names but different owners.
#         WHEN: ExpenseViewSet detail view called with PATCH by User belonging to Budget
#         with "owner" in payload, ending up with two the same Expense name for single owner.
#         THEN: Bad request HTTP 400, Expense not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_1 = expense_factory(budget=budget, **self.PAYLOAD, owner=base_user)
#         transfer_2 = expense_factory(budget=budget, **self.PAYLOAD, owner=None)
#         update_payload = {"owner": transfer_1.owner.id}
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer_2.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#
#     def test_transfer_update_many_fields(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database. Valid payload with many params.
#         WHEN: ExpenseViewSet detail endpoint called with PATCH.
#         THEN: HTTP 200 returned. Expense updated in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload = self.PAYLOAD.copy()
#         payload["owner"] = None
#         transfer = expense_factory(budget=budget, **payload)
#         update_payload = {
#             "name": "Some expense",
#             "description": "Updated expense description.",
#             "is_active": True,
#             "priority": ExpensePriority.DEBTS,
#             "owner": base_user.pk,
#         }
#
#         url = transfer_detail_url(transfer.budget.id, transfer.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         transfer.refresh_from_db()
#         for param, value in update_payload.items():
#             if param == "owner":
#                 continue
#             assert getattr(transfer, param) == value
#         assert transfer.owner == base_user
#
#
# @pytest.mark.django_db
# class TestExpenseViewSetDelete:
#     """Tests for delete Expense on ExpenseViewSet."""
#
#     def test_auth_required(
#         self, api_client: APIClient, base_user: AbstractUser, expense_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database.
#         WHEN: ExpenseViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         transfer = expense_factory()
#         url = transfer_detail_url(transfer.budget.id, transfer.id)
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
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database.
#         WHEN: ExpenseViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         transfer = expense_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(transfer.budget.id, transfer.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data["detail"] == "User does not have access to Budget."
#
#     def test_delete_transfer(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         expense_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Expense instance for Budget created in database.
#         WHEN: ExpenseViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, Expense deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer = expense_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = transfer_detail_url(budget.id, transfer.id)
#
#         assert budget.transfer_transfers.filter(transfer_type=CategoryType.EXPENSE).count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not budget.transfer_transfers.filter(transfer_type=CategoryType.EXPENSE).exists()
