from typing import Any

import pytest
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from budgets.models.budget_model import Budget
from categories.models.expense_category_model import ExpenseCategory
from categories.models.transfer_category_choices import CategoryType, ExpenseCategoryPriority
from categories.models.transfer_category_model import TransferCategory
from categories.serializers.expense_category_serializer import ExpenseCategorySerializer


def categories_url(budget_id):
    """Create and return an ExpenseCategory detail URL."""
    return reverse("budgets:expense_category-list", args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return an ExpenseCategory detail URL."""
    return reverse("budgets:expense_category-detail", args=[budget_id, category_id])


@pytest.mark.django_db
class TestExpenseCategoryViewSetList:
    """Tests for list view on ExpenseCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(categories_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet list view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(categories_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_category_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpenseCategory model instances for single Budget created in database.
        WHEN: ExpenseCategoryViewSet called by Budget owner.
        THEN: Response with serialized Budget ExpenseCategory list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            expense_category_factory(budget=budget)

        response = api_client.get(categories_url(budget.id))

        categories = ExpenseCategory.objects.filter(budget=budget)
        serializer = ExpenseCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_categories_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpenseCategory model instances for different Budgets created in database.
        WHEN: ExpenseCategoryViewSet called by one of Budgets owner.
        THEN: Response with serialized ExpenseCategory list (only from given Budget) returned.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget)
        expense_category_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        categories = ExpenseCategory.objects.filter(budget=budget)
        serializer = ExpenseCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == category.id

    def test_income_categories_not_in_expense_categories_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One ExpenseCategory and one IncomeCategory models instances for the same Budget created in database.
        WHEN: ExpenseCategoryViewSet called by one of Budgets owner.
        THEN: Response with serialized ExpenseCategory list (only from given Budget) returned without IncomeCategory.
        """
        budget = budget_factory(owner=base_user)
        expense_category_factory(budget=budget)
        income_category = income_category_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        expense_categories = ExpenseCategory.objects.filter(budget=budget)
        serializer = ExpenseCategorySerializer(expense_categories, many=True)
        assert TransferCategory.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == expense_categories.count() == 1
        assert response.data["results"] == serializer.data
        assert income_category.id not in [category["id"] for category in response.data["results"]]

    @pytest.mark.parametrize(
        "sort_param",
        ("id", "-id", "name", "-name", "owner__name", "-owner__name", "priority", "-priority"),
    )
    def test_get_categories_list_sorted_by_param(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        sort_param: str,
    ):
        """
        GIVEN: Five ExpenseCategory objects created in database.
        WHEN: The ExpenseCategoryViewSet list view is called with sorting by given param and without any filters.
        THEN: Response must contain all ExpenseCategory existing in database sorted by given param.
        """
        member_1 = user_factory(name="Bob")
        member_2 = user_factory(name="Alice")
        member_3 = user_factory(name="George")
        budget = budget_factory(owner=member_1, members=[member_1, member_2, member_3])
        expense_category_factory(
            budget=budget, name="Eee", owner=member_1, priority=ExpenseCategoryPriority.MOST_IMPORTANT
        )
        expense_category_factory(budget=budget, name="Ddd", owner=None, priority=ExpenseCategoryPriority.MOST_IMPORTANT)
        expense_category_factory(budget=budget, name="Ccc", owner=member_2, priority=ExpenseCategoryPriority.DEBTS)
        expense_category_factory(budget=budget, name="Bbb", owner=member_3, priority=ExpenseCategoryPriority.SAVINGS)
        expense_category_factory(budget=budget, name="Aaa", owner=None, priority=ExpenseCategoryPriority.OTHERS)
        api_client.force_authenticate(member_1)

        response = api_client.get(categories_url(budget.id), data={"ordering": sort_param})

        assert response.status_code == status.HTTP_200_OK
        categories = ExpenseCategory.objects.all().order_by(sort_param)
        serializer = ExpenseCategorySerializer(categories, many=True)
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == len(categories) == 5
        assert response.data["results"] == serializer.data

    @pytest.mark.parametrize(
        "filter_value",
        (
            "Some category",
            "SOME CATEGORY",
            "some category",
            "SoMe CaTeGoRy",
            "Some",
            "some",
            "SOME",
            "Category",
            "category",
            "CATEGORY",
        ),
    )
    def test_get_categories_list_filtered_by_name(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        filter_value: str,
    ):
        """
        GIVEN: Two ExpenseCategory objects for single Budget.
        WHEN: The ExpenseCategoryViewSet list view is called with period_id filter.
        THEN: Response must contain all ExpenseCategory existing in database assigned to Budget matching given
        period_id value.
        """
        budget = budget_factory(owner=base_user)
        matching_category = expense_category_factory(budget=budget, name="Some category")
        expense_category_factory(budget=budget, name="Other one")
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"name": filter_value})

        assert response.status_code == status.HTTP_200_OK
        assert ExpenseCategory.objects.all().count() == 2
        categories = ExpenseCategory.objects.filter(budget=budget, id=matching_category.id)
        serializer = ExpenseCategorySerializer(
            categories,
            many=True,
        )
        assert response.data["results"] and serializer.data
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == matching_category.id

    def test_get_categories_list_filtered_by_common_only(self):
        # TODO
        assert False

    def test_get_categories_list_filtered_by_owner(self):
        # TODO
        assert False

    def test_get_categories_list_filtered_by_is_active(self):
        # TODO
        assert False

    def test_get_categories_list_filtered_by_priority(self):
        # TODO
        assert False


@pytest.mark.django_db
class TestExpenseCategoryViewSetCreate:
    """Tests for create ExpenseCategory on ExpenseCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Bills",
        "description": "Expenses for bills.",
        "is_active": True,
        "priority": ExpenseCategoryPriority.MOST_IMPORTANT,
    }

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(categories_url(budget.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.post(categories_url(budget.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_create_single_category_without_owner(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for ExpenseCategory.
        WHEN: ExpenseCategoryViewSet called with POST by User belonging to Budget with valid payload.
        THEN: ExpenseCategory object created in database with given payload
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)

        response = api_client.post(categories_url(budget.id), data=self.PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert TransferCategory.expense_categories.filter(budget=budget).count() == 1
        assert TransferCategory.income_categories.filter(budget=budget).count() == 0
        category = ExpenseCategory.objects.get(id=response.data["id"])
        assert category.budget == budget
        for key in self.PAYLOAD:
            assert getattr(category, key) == self.PAYLOAD[key]
        serializer = ExpenseCategorySerializer(category)
        assert response.data == serializer.data

    def test_create_single_category_with_owner(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for ExpenseCategory.
        WHEN: ExpenseCategoryViewSet called with POST by User belonging to Budget with valid payload.
        THEN: ExpenseCategory object created in database with given payload
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = base_user.id

        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1
        assert TransferCategory.expense_categories.filter(budget=budget).count() == 1
        assert TransferCategory.income_categories.filter(budget=budget).count() == 0
        category = ExpenseCategory.objects.get(id=response.data["id"])
        assert category.budget == budget
        for key in payload:
            if key == "owner":
                continue
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner == base_user
        serializer = ExpenseCategorySerializer(category)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for ExpenseCategory with field value too long.
        WHEN: ExpenseCategoryViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. ExpenseCategory not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = ExpenseCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not ExpenseCategory.objects.filter(budget=budget).exists()

    def test_error_name_already_used_for_common_category(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for ExpenseCategory.
        WHEN: ExpenseCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one ExpenseCategory created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Common ExpenseCategory with given name already exists in Budget."
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1

    def test_error_name_already_used_for_personal_category(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for ExpenseCategory.
        WHEN: ExpenseCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one ExpenseCategory created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = base_user.id

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Personal ExpenseCategory with given name already exists in Budget."
        )
        assert ExpenseCategory.objects.filter(budget=budget).count() == 1

    def test_error_invalid_priority(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for ExpenseCategory.
        WHEN: ExpenseCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one ExpenseCategory created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["priority"] = ExpenseCategoryPriority.values[-1] + 1

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "priority" in response.data["detail"]
        assert response.data["detail"]["priority"][0] == f"\"{payload['priority']}\" is not a valid choice."
        assert not ExpenseCategory.objects.filter(budget=budget).exists()


@pytest.mark.django_db
class TestExpenseCategoryViewSetDetail:
    """Tests for detail view on ExpenseCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, expense_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = expense_category_factory()
        res = api_client.get(category_detail_url(category.budget.id, category.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet detail view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        category = expense_category_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_get_category_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database.
        WHEN: ExpenseCategoryViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, ExpenseCategory details returned.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.get(url)
        serializer = ExpenseCategorySerializer(category)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestExpenseCategoryViewSetUpdate:
    """Tests for update view on ExpenseCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Bills",
        "description": "Expenses for bills.",
        "is_active": True,
        "priority": ExpenseCategoryPriority.MOST_IMPORTANT,
    }

    def test_auth_required(self, api_client: APIClient, expense_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = expense_category_factory()
        res = api_client.patch(category_detail_url(category.budget.id, category.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        category = expense_category_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.patch(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", "New name"),
            ("description", "New description"),
            ("is_active", not PAYLOAD["is_active"]),
            ("priority", ExpenseCategoryPriority.DEBTS),
        ],
    )
    @pytest.mark.django_db
    def test_category_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, ExpenseCategory updated.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, param) == update_payload[param]

    def test_error_on_category_name_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpenseCategory instances for Budget created in database. Update payload with invalid "name" value.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, ExpenseCategory not updated.
        """
        budget = budget_factory(owner=base_user)
        category_1 = expense_category_factory(budget=budget, **self.PAYLOAD, owner=None)
        category_2 = expense_category_factory(budget=budget, owner=None)
        old_value = getattr(category_2, "name")
        update_payload = {"name": category_1.name}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category_2.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category_2.refresh_from_db()
        assert getattr(category_2, "name") == old_value

    def test_error_on_category_priority_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpenseCategory instances for Budget created in database. Update payload with invalid "priority"
        value.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, ExpenseCategory not updated.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget, owner=None)
        old_value = getattr(category, "priority")
        update_payload = {"priority": ExpenseCategoryPriority.values[-1] + 1}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category.refresh_from_db()
        assert getattr(category, "priority") == old_value

    def test_error_on_category_owner_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two ExpenseCategory instances for Budget created in database with the same names but different owners.
        WHEN: ExpenseCategoryViewSet detail view called with PATCH by User belonging to Budget
        with "owner" in payload, ending up with two the same ExpenseCategory name for single owner.
        THEN: Bad request HTTP 400, ExpenseCategory not updated.
        """
        budget = budget_factory(owner=base_user)
        category_1 = expense_category_factory(budget=budget, **self.PAYLOAD, owner=base_user)
        category_2 = expense_category_factory(budget=budget, **self.PAYLOAD, owner=None)
        update_payload = {"owner": category_1.owner.id}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category_2.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_category_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database. Valid payload with many params.
        WHEN: ExpenseCategoryViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. ExpenseCategory updated in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = None
        category = expense_category_factory(budget=budget, **payload)
        update_payload = {
            "name": "Some expense",
            "description": "Updated expense description.",
            "is_active": True,
            "priority": ExpenseCategoryPriority.DEBTS,
            "owner": base_user.pk,
        }

        url = category_detail_url(category.budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        for param, value in update_payload.items():
            if param == "owner":
                continue
            assert getattr(category, param) == value
        assert category.owner == base_user


@pytest.mark.django_db
class TestExpenseCategoryViewSetDelete:
    """Tests for delete ExpenseCategory on ExpenseCategoryViewSet."""

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, expense_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database.
        WHEN: ExpenseCategoryViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        category = expense_category_factory()
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database.
        WHEN: ExpenseCategoryViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        category = expense_category_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_delete_category(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: ExpenseCategory instance for Budget created in database.
        WHEN: ExpenseCategoryViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, ExpenseCategory deleted.
        """
        budget = budget_factory(owner=base_user)
        category = expense_category_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        assert budget.transfer_categories.filter(category_type=CategoryType.EXPENSE).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not budget.transfer_categories.filter(category_type=CategoryType.EXPENSE).exists()
