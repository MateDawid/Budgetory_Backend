from typing import Any

import pytest
from categories_tests.utils import (
    INVALID_TYPE_AND_PRIORITY_COMBINATIONS,
    VALID_TYPE_AND_PRIORITY_COMBINATIONS,
    annotate_transfer_category_queryset,
)
from conftest import get_jwt_access_token
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient

from app_users.models import User
from budgets.models.budget_model import Budget
from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


def categories_url(budget_id):
    """Create and return an TransferCategory detail URL."""
    return reverse("budgets:category-list", args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return an TransferCategory detail URL."""
    return reverse("budgets:category-detail", args=[budget_id, category_id])


@pytest.mark.django_db
class TestTransferCategoryViewSetList:
    """Tests for list view on TransferCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet list view called with GET without authentication.
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
        WHEN: TransferCategoryViewSet list endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        url = categories_url(budget.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_get_response_without_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten TransferCategory model instances for single Budget created in database.
        WHEN: TransferCategoryViewSet called by Budget member without pagination parameters.
        THEN: HTTP 200 - Response with all objects returned.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(10):
            transfer_category_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        assert response.status_code == status.HTTP_200_OK
        assert "results" not in response.data
        assert "count" not in response.data
        assert len(response.data) == 10

    def test_get_response_with_pagination(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Ten TransferCategory model instances for single Budget created in database.
        WHEN: TransferCategoryViewSet called by Budget member with pagination parameters - page_size and page.
        THEN: HTTP 200 - Paginated response returned.
        """
        budget = budget_factory(members=[base_user])
        for _ in range(10):
            transfer_category_factory(budget=budget)
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id), data={"page_size": 2, "page": 1})

        assert response.status_code == status.HTTP_200_OK
        assert "results" in response.data
        assert response.data["count"] == 10

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet list view called with GET by User not belonging to given Budget.
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
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory model instances for single Budget created in database.
        WHEN: TransferCategoryViewSet called by Budget owner.
        THEN: Response with serialized Budget TransferCategory list returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        transfer_category_factory(budget=budget)
        transfer_category_factory(budget=budget)

        response = api_client.get(categories_url(budget.id))

        categories = annotate_transfer_category_queryset(
            TransferCategory.objects.prefetch_related("budget", "deposit").filter(budget=budget)
        ).distinct()
        serializer = TransferCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(serializer.data) == 2
        assert response.data == serializer.data
        for category in serializer.data:
            assert category["value"] == category["id"]
            assert (
                category["label"]
                == f"{'📉' if category['category_type'] == CategoryType.EXPENSE else '📈'} {category['name']}"
            )
            assert category["deposit_display"] == categories.get(id=category["id"]).deposit_display
            assert category["priority_display"] == CategoryPriority(category["priority"]).label
            assert category["category_type_display"] == CategoryType(category["category_type"]).label

    def test_categories_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory model instances for different Budgets created in database.
        WHEN: TransferCategoryViewSet called by one of Budgets owner.
        THEN: Response with serialized TransferCategory list (only from given Budget) returned.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        transfer_category_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(categories_url(budget.id))

        categories = annotate_transfer_category_queryset(TransferCategory.objects.filter(budget=budget))
        serializer = TransferCategorySerializer(categories, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(serializer.data) == categories.count() == 1
        assert response.data == serializer.data
        assert response.data[0]["id"] == category.id


@pytest.mark.django_db
class TestTransferCategoryViewSetCreate:
    """Tests for create TransferCategory on TransferCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Bills",
        "description": "Transfers for bills.",
        "is_active": True,
        "category_type": CategoryType.EXPENSE,
        "priority": CategoryPriority.MOST_IMPORTANT,
    }

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet list view called with POST without authentication.
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
        WHEN: TransferCategoryViewSet list endpoint called with POST.
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
        WHEN: TransferCategoryViewSet list view called with POST by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        api_client.force_authenticate(other_user)

        response = api_client.post(categories_url(budget.id), data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_create_single_category(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for TransferCategory.
        WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with valid payload.
        THEN: TransferCategory object created in database with given payload.
        """
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        budget = budget_factory(members=[base_user])
        payload["deposit"] = deposit_factory(budget=budget).id
        api_client.force_authenticate(base_user)

        response = api_client.post(categories_url(budget.id), data=payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        category = TransferCategory.objects.get(id=response.data["id"])
        assert category.budget == budget
        assert category.deposit.id == payload["deposit"]
        for key in payload:
            if key == "deposit":
                continue
            assert getattr(category, key) == payload[key]
        serializer = TransferCategorySerializer(category)
        assert response.data == serializer.data

    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for TransferCategory with field value too long.
        WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. TransferCategory not created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        max_length = TransferCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"

        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data["detail"]
        assert response.data["detail"][field_name][0] == f"Ensure this field has no more than {max_length} characters."
        assert not TransferCategory.objects.filter(budget=budget).exists()

    def test_error_name_already_used(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for TransferCategory.
        WHEN: TransferCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one TransferCategory created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit_factory(budget=budget).id

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0]
            == "Transfer Category for Deposit with given name already exists."
        )
        assert TransferCategory.objects.filter(budget=budget).count() == 1

    @pytest.mark.parametrize("category_type, priority", INVALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_error_invalid_priority_for_type(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for TransferCategory.
        WHEN: TransferCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one TransferCategory created in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        payload["category_type"] = category_type
        payload["priority"] = priority
        payload["deposit"] = deposit_factory(budget=budget).id

        api_client.post(categories_url(budget.id), payload)
        response = api_client.post(categories_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non_field_errors" in response.data["detail"]
        assert (
            response.data["detail"]["non_field_errors"][0] == "Invalid priority selected for specified Category type."
        )
        assert not TransferCategory.objects.filter(budget=budget).exists()


@pytest.mark.django_db
class TestTransferCategoryViewSetDetail:
    """Tests for detail view on TransferCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet detail view called with GET without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = transfer_category_factory()
        res = api_client.get(category_detail_url(category.budget.id, category.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferCategoryViewSet detail endpoint called with GET.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.get(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet detail view called with GET by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        category = transfer_category_factory(budget=budget)
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
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, TransferCategory details returned.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        setattr(category, "deposit_display", getattr(getattr(category, "deposit", None), "name", None))
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.get(url)
        serializer = TransferCategorySerializer(category)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data


@pytest.mark.django_db
class TestTransferCategoryViewSetUpdate:
    """Tests for update view on TransferCategoryViewSet."""

    PAYLOAD: dict[str, Any] = {
        "name": "Bills",
        "description": "Transfers for bills.",
        "is_active": True,
        "category_type": CategoryType.EXPENSE,
        "priority": CategoryPriority.MOST_IMPORTANT,
    }

    def test_auth_required(self, api_client: APIClient, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet detail view called with PATCH without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        category = transfer_category_factory()
        res = api_client.patch(category_detail_url(category.budget.id, category.id), data={})

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferCategoryViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.patch(url, data={}, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_200_OK

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(members=[budget_owner])
        category = transfer_category_factory(budget=budget)
        api_client.force_authenticate(other_user)
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.patch(url, data={})

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data["detail"] == "User does not have access to Budget."

    @pytest.mark.parametrize(
        "param, value",
        [
            ("name", "New name"),
            ("description", "New description"),
            ("is_active", not PAYLOAD["is_active"]),
            ("priority", CategoryPriority.OTHERS),
        ],
    )
    @pytest.mark.django_db
    def test_category_update(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, TransferCategory updated.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget, **self.PAYLOAD)
        update_payload = {param: value}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, param) == update_payload[param]

    @pytest.mark.django_db
    @pytest.mark.parametrize("category_type, priority", VALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_category_update_category_type_and_priority(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget.
        THEN: HTTP 200, TransferCategory updated.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget, **self.PAYLOAD)
        update_payload = {"category_type": category_type, "priority": priority}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, "category_type") == update_payload["category_type"]
        assert getattr(category, "priority") == update_payload["priority"]

    @pytest.mark.django_db
    def test_category_update_deposit(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget with deposit id value
        for 'deposit' field.
        THEN: HTTP 200, TransferCategory updated, "deposit" value for Category is updated.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget, **self.PAYLOAD)
        new_deposit = deposit_factory(budget=budget)
        update_payload = {"deposit": new_deposit.id}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, "deposit") == new_deposit

    def test_error_on_category_name_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategory instances for Budget created in database. Update payload with invalid "name" value.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, TransferCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        deposit = deposit_factory(budget=budget)
        category_1 = transfer_category_factory(budget=budget, deposit=deposit, **self.PAYLOAD)
        category_2 = transfer_category_factory(budget=budget, deposit=deposit)
        old_value = getattr(category_2, "name")
        update_payload = {"name": category_1.name}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category_2.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category_2.refresh_from_db()
        assert getattr(category_2, "name") == old_value

    @pytest.mark.parametrize("category_type, priority", INVALID_TYPE_AND_PRIORITY_COMBINATIONS)
    def test_error_on_category_priority_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        category_type: CategoryType,
        priority: CategoryPriority,
    ):
        """
        GIVEN: Two TransferCategory instances for Budget created in database. Update payload with invalid "priority"
        value.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget
        with invalid payload.
        THEN: Bad request HTTP 400, TransferCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        old_type, old_priority = getattr(category, "category_type"), getattr(category, "priority")
        update_payload = {"category_type": category_type, "priority": priority}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category.refresh_from_db()
        assert getattr(category, "category_type") == old_type
        assert getattr(category, "priority") == old_priority

    def test_error_on_category_deposit_update(
        self,
        api_client: APIClient,
        base_user: Any,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instances for Budget created in database with valid deposit.
        WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget
        with Deposit from different Budget as "deposit" in payload.
        THEN: Bad request HTTP 400, TransferCategory not updated.
        """
        budget = budget_factory(members=[base_user])
        valid_deposit = deposit_factory(budget=budget)
        invalid_deposit = deposit_factory(budget=budget_factory())
        category = transfer_category_factory(budget=budget, deposit=valid_deposit, **self.PAYLOAD)
        update_payload = {"deposit": invalid_deposit.id}
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_category_update_many_fields(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database. Valid payload with many params.
        WHEN: TransferCategoryViewSet detail endpoint called with PATCH.
        THEN: HTTP 200 returned. TransferCategory updated in database.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()
        category = transfer_category_factory(budget=budget, **payload)
        update_payload = {
            "name": "Some transfer",
            "description": "Updated transfer description.",
            "is_active": True,
            "priority": CategoryPriority.OTHERS,
            "deposit": deposit_factory(budget=budget).pk,
        }

        url = category_detail_url(category.budget.id, category.id)

        response = api_client.patch(url, update_payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.deposit.pk == update_payload["deposit"]
        for param, value in update_payload.items():
            if param == "deposit":
                continue
            assert getattr(category, param) == value


@pytest.mark.django_db
class TestTransferCategoryViewSetDelete:
    """Tests for delete TransferCategory on TransferCategoryViewSet."""

    def test_auth_required(
        self, api_client: APIClient, base_user: AbstractUser, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with PUT without authentication.
        THEN: Unauthorized HTTP 401.
        """
        category = transfer_category_factory()
        url = category_detail_url(category.budget.id, category.id)

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_with_jwt(
        self,
        api_client: APIClient,
        base_user: User,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Users JWT in request headers as HTTP_AUTHORIZATION.
        WHEN: TransferCategoryViewSet detail endpoint called with DELETE.
        THEN: HTTP 204 returned.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        url = category_detail_url(category.budget.id, category.id)
        jwt_access_token = get_jwt_access_token(user=base_user)
        response = api_client.delete(url, HTTP_AUTHORIZATION=f"Bearer {jwt_access_token}")
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_user_not_budget_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with DELETE by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        category = transfer_category_factory(budget=budget_factory())
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
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: TransferCategory instance for Budget created in database.
        WHEN: TransferCategoryViewSet detail view called with DELETE by User belonging to Budget.
        THEN: No content HTTP 204, TransferCategory deleted.
        """
        budget = budget_factory(members=[base_user])
        category = transfer_category_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = category_detail_url(budget.id, category.id)

        assert budget.transfer_categories.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not budget.transfer_categories.all().exists()
