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
from categories.models.choices.transfer_category_choices import CategoryType, IncomeCategoryPriority
from categories.models.income_category_model import IncomeCategory
from categories.models.transfer_category_model import TransferCategory
from categories.serializers.income_category_serializer import IncomeCategorySerializer


def categories_url(budget_id):
    """Create and return an IncomeCategory detail URL."""
    return reverse("budgets:income_category-list", args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return an IncomeCategory detail URL."""
    return reverse("budgets:income_category-detail", args=[budget_id, category_id])


@pytest.mark.django_db
class TestIncomeCategoryViewSetList:
    """Tests for list view on IncomeCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet list view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(categories_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeCategoryViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = categories_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet list view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        api_client.force_authenticate(other_user)

        response = api_client.get(categories_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_retrieve_category_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory model instances for single Budget created in database.
        WHEN: IncomeCategoryViewSet called by Budget owner.
        THEN: Response with serialized Budget IncomeCategory list returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        for _ in range(2):
            income_category_factory(budget=budget)

        response = api_client.get(categories_url(budget.id))

        categories = IncomeCategory.objects.filter(budget=budget)
        serializer = IncomeCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["results"] == serializer.data

    def test_categories_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory model instances for different Budgets created in database.
        WHEN: IncomeCategoryViewSet called by one of Budgets owner.
        THEN: Response with serialized IncomeCategory list (only from given Budget) returned.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        income_category_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        categories = IncomeCategory.objects.filter(budget=budget)
        serializer = IncomeCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == categories.count() == 1
        assert response.data["results"] == serializer.data
        assert response.data["results"][0]["id"] == category.id

    def test_income_categories_not_in_income_categories_list(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: One IncomeCategory and one IncomeCategory models instances for the same Budget created in database.
        WHEN: IncomeCategoryViewSet called by one of Budgets owner.
        THEN: Response with serialized IncomeCategory list (only from given Budget) returned without IncomeCategory.
        """
        budget = budget_factory(members=[base_user])
        income_category_factory(budget=budget)
        expense_category = expense_category_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        income_categories = IncomeCategory.objects.filter(budget=budget)
        serializer = IncomeCategorySerializer(income_categories, many=True)
        assert TransferCategory.objects.all().count() == 2
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == len(serializer.data) == income_categories.count() == 1
        assert response.data["results"] == serializer.data
        assert expense_category.id not in [category["id"] for category in response.data["results"]]


@pytest.mark.django_db
class TestIncomeCategoryViewSetCreate:
    """Tests for create IncomeCategory on IncomeCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Salary",
        "description": "Salary incomes.",
        "is_active": True,
        "priority": IncomeCategoryPriority.REGULAR,
    }

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet list view called with POST without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.post(categories_url(budget.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeCategoryViewSet list endpoint called with POST.
        THEN: HTTP 400 returned - access granted, but invalid input.
        """
        budget = budget_factory(members=[base_user])
        url = categories_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.post(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        api_client.force_authenticate(other_user)

        response = api_client.post(categories_url(budget.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    def test_create_single_category_without_owner(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for IncomeCategory.
        WHEN: IncomeCategoryViewSet called with POST by User belonging to Budget with valid payload.
        THEN: IncomeCategory object created in database with given payload
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)

        response = api_client.post(categories_url(budget.id), data=self.PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert TransferCategory.income_categories.filter(budget=budget).count() == 1
        assert TransferCategory.expense_categories.filter(budget=budget).count() == 0
        category = IncomeCategory.objects.get(id=response.data["id"])
        assert category.budget == budget
        for key in self.PAYLOAD:
            assert getattr(category, key) == self.PAYLOAD[key]
        serializer = IncomeCategorySerializer(category)
        assert response.data == serializer.data

    def test_create_single_category_with_owner(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for IncomeCategory.
        WHEN: IncomeCategoryViewSet called with POST by User belonging to Budget with valid payload.
        THEN: IncomeCategory object created in database with given payload
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = base_user.id

        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert IncomeCategory.objects.filter(budget=budget).count() == 1
        assert TransferCategory.income_categories.filter(budget=budget).count() == 1
        assert TransferCategory.expense_categories.filter(budget=budget).count() == 0
        category = IncomeCategory.objects.get(id=response.data["id"])
        assert category.budget == budget
        for key in payload:
            if key == "owner":
                continue
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner == base_user
        serializer = IncomeCategorySerializer(category)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for IncomeCategory with field value too long.
        WHEN: IncomeCategoryViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. IncomeCategory not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = IncomeCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not IncomeCategory.objects.filter(budget=budget).exists()

    def test_error_name_already_used_for_common_category(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for IncomeCategory.
        WHEN: IncomeCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one IncomeCategory created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Common IncomeCategory with given name already exists in Budget."
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1

    def test_error_name_already_used_for_personal_category(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for IncomeCategory.
        WHEN: IncomeCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one IncomeCategory created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = base_user.id

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Personal IncomeCategory with given name already exists in Budget."
        )
        assert IncomeCategory.objects.filter(budget=budget).count() == 1

    def test_error_invalid_priority(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for IncomeCategory.
        WHEN: IncomeCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one IncomeCategory created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["priority"] = IncomeCategoryPriority.values[-1] + 1

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "priority" in response.data["detail"]
        assert response.data["detail"]["priority"][0] == f"\"{payload['priority']}\" is not a valid choice."
        assert not IncomeCategory.objects.filter(budget=budget).exists()


@pytest.mark.django_db
class TestIncomeCategoryViewSetDetail:
    """Tests for detail view on IncomeCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, income_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = income_category_factory()
        res = api_client.get(category_detail_url(category.budget.id, category.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeCategoryViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet detail view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        category = income_category_factory(budget=budget)
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database.
        WHEN: IncomeCategoryViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, IncomeCategory details returned.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.get(url)
        serializer = IncomeCategorySerializer(category)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestIncomeCategoryViewSetUpdate:
    """Tests for update view on IncomeCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Salary",
        "description": "Salary incomes.",
        "is_active": True,
        "priority": IncomeCategoryPriority.REGULAR,
    }

    def test_auth_required(self, api_client: APIClient, income_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = income_category_factory()
        res = api_client.patch(category_detail_url(category.budget.id, category.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeCategoryViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: IncomeCategoryViewSet detail view called with PATCH by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        category = income_category_factory(budget=budget)
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
            ("priority", IncomeCategoryPriority.IRREGULAR),
        ],
    )
    @pytest.mark.django_db
    def test_category_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database.
        WHEN: IncomeCategoryViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, IncomeCategory updated.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget, **self.PAYLOAD)
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory instances for Budget created in database. Update payload with invalid "name" value.
        WHEN: IncomeCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, IncomeCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        category_1 = income_category_factory(budget=budget, **self.PAYLOAD, owner=None)
        category_2 = income_category_factory(budget=budget, owner=None)
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory instances for Budget created in database. Update payload with invalid "priority"
        value.
        WHEN: IncomeCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, IncomeCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget, owner=None)
        old_value = getattr(category, "priority")
        update_payload = {"priority": IncomeCategoryPriority.values[-1] + 1}
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two IncomeCategory instances for Budget created in database with the same names but different owners.
        WHEN: IncomeCategoryViewSet detail view called with PATCH by User belonging to Budget
        with "owner" in payload, ending up with two the same IncomeCategory name for single owner.
        THEN: Bad request HTTP 400, IncomeCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        category_1 = income_category_factory(budget=budget, **self.PAYLOAD, owner=base_user)
        category_2 = income_category_factory(budget=budget, **self.PAYLOAD, owner=None)
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database. Valid payload with many params.
        WHEN: IncomeCategoryViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. IncomeCategory updated in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["owner"] = None
        category = income_category_factory(budget=budget, **payload)
        update_payload = {
            "name": "Some income",
            "description": "Updated income description.",
            "is_active": True,
            "priority": IncomeCategoryPriority.IRREGULAR,
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
class TestIncomeCategoryViewSetDelete:
    """Tests for delete IncomeCategory on IncomeCategoryViewSet."""

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, income_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database.
        WHEN: IncomeCategoryViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        category = income_category_factory()
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: IncomeCategoryViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database.
        WHEN: IncomeCategoryViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        category = income_category_factory(budget=budget_factory())
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
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: IncomeCategory instance for Budget created in database.
        WHEN: IncomeCategoryViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, IncomeCategory deleted.
        """
        budget = budget_factory(members=[base_user])
        category = income_category_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        assert budget.transfer_categories.filter(category_type=CategoryType.INCOME).count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not budget.transfer_categories.filter(category_type=CategoryType.INCOME).exists()
