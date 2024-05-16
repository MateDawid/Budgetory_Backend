from dataclasses import dataclass
from typing import Callable, Protocol

import pytest
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient
from transfers.models import TransferCategory
from transfers.serializers import (
    ExpenseCategorySerializer,
    IncomeCategorySerializer,
    TransferCategorySerializer,
)


def expense_category_url(budget_id: int):
    """Create and return an EXPENSE TransferCategory list URL."""
    return reverse('budgets:expense_category-list', args=[budget_id])


def income_category_url(budget_id: int):
    """Create and return an INCOME TransferCategory list URL."""
    return reverse('budgets:income_category-list', args=[budget_id])


def expense_category_detail_url(budget_id: int, category_id: int):
    """Create and return an EXPENSE TransferCategory detail URL."""
    return reverse('budgets:expense_category-detail', args=[budget_id, category_id])


def income_category_detail_url(budget_id: int, category_id: int):
    """Create and return an INCOME TransferCategory detail URL."""
    return reverse('budgets:income_category-detail', args=[budget_id, category_id])


class TransferCategoryTestParams(Protocol):
    serializer: TransferCategorySerializer
    list_url: Callable
    detail_url: Callable


@dataclass
class ExpenseCategoryTestParams:
    serializer: TransferCategorySerializer = ExpenseCategorySerializer
    list_url: Callable = expense_category_url
    detail_url: Callable = expense_category_detail_url


@dataclass
class IncomeCategoryTestParams:
    serializer: TransferCategorySerializer = IncomeCategorySerializer
    list_url: Callable[[int], str] = income_category_url
    detail_url: Callable[[int, int], str] = income_category_detail_url


@pytest.mark.django_db
class TestTransferCategoryApiAccess:
    """Tests for access to TransferCategoryViewSet."""

    @pytest.mark.parametrize('url', [IncomeCategoryTestParams.list_url, ExpenseCategoryTestParams.list_url])
    def test_auth_required_on_list_view(
        self, api_client: APIClient, transfer_category: TransferCategory, url: Callable[[int], str]
    ):
        """
        GIVEN: TransferCategory model instance in database.
        WHEN: TransferCategoryViewSet list method called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(url(transfer_category.budget.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('url', [IncomeCategoryTestParams.detail_url, ExpenseCategoryTestParams.detail_url])
    def test_auth_required_on_detail_view(
        self, api_client: APIClient, transfer_category: TransferCategory, url: Callable[[int, int], str]
    ):
        """
        GIVEN: TransferCategory model instance in database.
        WHEN: TransferCategoryViewSet detail method called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        response = api_client.get(url(transfer_category.budget.id, transfer_category.id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize('url', [IncomeCategoryTestParams.list_url, ExpenseCategoryTestParams.list_url])
    def test_user_not_budget_member_on_list_view(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        url: Callable[[int], str],
    ):
        """
        GIVEN: TransferCategory model instance in database.
        WHEN: TransferCategoryViewSet list method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        transfer_category = transfer_category_factory(budget__owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(url(transfer_category.budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'

    @pytest.mark.parametrize('url', [IncomeCategoryTestParams.detail_url, ExpenseCategoryTestParams.detail_url])
    def test_user_not_budget_member_on_detail_view(
        self,
        api_client: APIClient,
        user_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        url: Callable[[int, int], str],
    ):
        """
        GIVEN: TransferCategory model instance in database.
        WHEN: TransferCategoryViewSet detail method called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        transfer_category = transfer_category_factory(budget__owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(url(transfer_category.budget.id, transfer_category.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


# @pytest.mark.django_db
# class TestTransferCategoryApiList:
#     """Tests for list view on TransferCategoryViewSet."""
#
#     @pytest.mark.parametrize('url_name, ')
#     def test_retrieve_category_list_by_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two TransferCategory model instances for single Budget created in database.
#         WHEN: TransferCategoryViewSet called by Budget owner.
#         THEN: Response with serialized Budget TransferCategory list returned.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             transfer_category_factory(group__budget=budget)
#
#         response = api_client.get(category_url(budget.id))
#
#         categories = TransferCategory.objects.filter(group__budget=budget)
#         serializer = TransferCategorySerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_retrieve_category_list_by_member(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two TransferCategory model instances for single Budget created in database.
#         WHEN: TransferCategoryViewSet called by Budget member.
#         THEN: Response with serialized Budget TransferCategory list returned.
#         """
#         budget = budget_factory(members=[base_user])
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             transfer_category_factory(group__budget=budget)
#
#         response = api_client.get(category_url(budget.id))
#
#         categories = TransferCategory.objects.filter(group__budget=budget)
#         serializer = TransferCategorySerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_category_list_limited_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two TransferCategory model instances for different Budgets created in database.
#         WHEN: TransferCategoryViewSet called by one of Budgets owner.
#         THEN: Response with serialized TransferCategory list (only from given Budget) returned.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         transfer_category_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(category_url(budget.id))
#
#         categories = TransferCategory.objects.filter(group__budget=budget)
#         serializer = TransferCategorySerializer(categories, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert len(response.data['results']) == len(serializer.data) == categories.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == category.id
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiCreate:
#     """Tests for create TransferCategory on TransferCategoryViewSet."""
#
#     PAYLOAD = {'name': 'Expenses for food', 'description': 'All money spent for food.', 'is_active': True}
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_create_single_category(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: Budget and TransferCategoryGroup instances created in database. Valid payload prepared
#         for TransferCategory.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: TransferCategory object created in database with given payload
#         """
#         other_user = user_factory()
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user, members=[other_user])
#         else:
#             budget = budget_factory(members=[base_user, other_user])
#         group = transfer_category_group_factory(budget=budget)
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert TransferCategory.objects.filter(group__budget=budget).count() == 1
#         category = TransferCategory.objects.get(id=response.data['id'])
#         assert category.group == group
#         for key in payload:
#             if key == 'group':
#                 continue
#             assert getattr(category, key) == self.PAYLOAD[key]
#         serializer = TransferCategorySerializer(category)
#         assert response.data == serializer.data
#
#     def test_create_category_with_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget and TransferCategoryGroup instances created in database. Valid payload with owner prepared
#         for TransferCategory.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: TransferCategory object created in database with given payload
#         """
#         budget = budget_factory(owner=base_user)
#         group = transfer_category_group_factory(budget=budget)
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         category = TransferCategory.objects.get(id=response.data['id'])
#         assert category.owner == base_user
#         assert base_user.personal_categories.filter(group__budget=budget).count() == 1
#         serializer = TransferCategorySerializer(category)
#         assert response.data == serializer.data
#
#     def test_create_two_categories_for_single_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Budget and TransferCategoryGroup instances created in database. Valid payloads prepared
#         for two TransferCategories.
#         WHEN: TransferCategoryViewSet called twice with POST by User belonging to Budget with valid payloads.
#         THEN: Two TransferCategory objects created in database with given payloads.
#         """
#         budget = budget_factory(owner=base_user)
#         group_1 = transfer_category_group_factory(budget=budget)
#         group_2 = transfer_category_group_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         payload_1 = self.PAYLOAD.copy()
#         payload_1['name'] = 'TransferCategory name 1'
#         payload_1['group'] = group_1.id
#         payload_2 = self.PAYLOAD.copy()
#         payload_2['name'] = 'TransferCategory name 2'
#         payload_2['group'] = group_2.id
#
#         response_1 = api_client.post(category_url(budget.id), payload_1)
#         response_2 = api_client.post(category_url(budget.id), payload_2)
#
#         assert response_1.status_code == status.HTTP_201_CREATED
#         assert response_2.status_code == status.HTTP_201_CREATED
#         assert TransferCategory.objects.filter(group__budget=budget).count() == 2
#         for response, payload, group in [(response_1, payload_1, group_1), (response_2, payload_2, group_2)]:
#             category = TransferCategory.objects.get(id=response.data['id'])
#             for key in payload:
#                 if key == 'group':
#                     assert category.group == group
#                 else:
#                     assert getattr(category, key) == payload[key]
#
#     def test_create_same_category_for_two_budgets(
#         self, api_client: APIClient, budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Two TransferCategoryGroup for two Budget instances created in database. Valid payload prepared for two
#         TransferCategories.
#         WHEN: TransferCategoryViewSet called twice with POST by different Users belonging to two different
#         Budgets with valid payload.
#         THEN: Two TransferCategory objects created in database with given payload for separate Budgets.
#         """
#         payload = self.PAYLOAD.copy()
#         budget_1 = budget_factory()
#         group_1 = transfer_category_group_factory(budget=budget_1)
#         budget_2 = budget_factory()
#         group_2 = transfer_category_group_factory(budget=budget_2)
#
#         api_client.force_authenticate(budget_1.owner)
#         payload['group'] = group_1.id
#         api_client.post(category_url(budget_1.id), payload)
#         api_client.force_authenticate(budget_2.owner)
#         payload['group'] = group_2.id
#         api_client.post(category_url(budget_2.id), payload)
#
#         assert TransferCategory.objects.all().count() == 2
#         assert TransferCategory.objects.filter(group__budget=budget_1).count() == 1
#         assert TransferCategory.objects.filter(group__budget=budget_2).count() == 1
#
#     @pytest.mark.parametrize('field_name', ['name', 'description'])
#     def test_error_value_too_long(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         field_name: str,
#     ):
#         """
#         GIVEN: TransferCategoryGroup for Budget instance created in database. Payload for TransferCategory with
#         field value too long.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         group = transfer_category_group_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         max_length = TransferCategory._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         payload[field_name] = (max_length + 1) * 'a'
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert field_name in response.data
#         assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
#         assert not TransferCategory.objects.filter(group__budget=budget).exists()
#
#     def test_error_create_category_for_not_accessible_budget(
#         self, api_client: APIClient, base_user: AbstractUser, transfer_category_group_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup for Budget instance created in database. Valid payload for TransferCategory.
#         WHEN: TransferCategoryViewSet called with POST by User not belonging to Budget with valid payload.
#         THEN: Forbidden HTTP 403 returned. Object not created.
#         """
#         group = transfer_category_group_factory()
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(category_url(group.budget.id), payload)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#         assert not TransferCategory.objects.filter(group__budget=group.budget).exists()
#
#     def test_error_group_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup and two Budget instances created in database. TransferCategoryGroup from outer
#         Budget in payload.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No TransferCategory created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         outer_group = transfer_category_group_factory()
#         payload = self.PAYLOAD.copy()
#         payload['group'] = outer_group.id
#         api_client.force_authenticate(base_user)
#
#         api_client.post(category_url(budget.id), payload)
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'TransferCategoryGroup does not belong to Budget.'
#         assert not TransferCategory.objects.filter(group__budget=budget).exists()
#
#     def test_error_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup for Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No TransferCategory created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         group = transfer_category_group_factory(budget=budget)
#         outer_user = user_factory()
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         payload['owner'] = outer_user.id
#         api_client.force_authenticate(base_user)
#
#         api_client.post(category_url(budget.id), payload)
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#         assert not TransferCategory.objects.filter(group__budget=budget).exists()
#
#     def test_error_personal_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         and owner of existing TransferCategory in payload.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No TransferCategory created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         group = transfer_category_group_factory(budget=budget)
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#         api_client.post(category_url(budget.id), payload)
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal TransferCategory with given name already exists in Budget for provided owner.'
#         )
#         assert TransferCategory.objects.filter(group__budget=budget, owner__isnull=False).count() == 1
#
#     def test_error_common_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         and owner of existing TransferCategory in payload.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. No TransferCategory created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         group = transfer_category_group_factory(budget=budget)
#         payload = self.PAYLOAD.copy()
#         payload['group'] = group.id
#         api_client.force_authenticate(base_user)
#         api_client.post(category_url(budget.id), payload)
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0] == 'Common TransferCategory with
#             given name already exists in Budget.'
#         )
#         assert TransferCategory.objects.filter(group__budget=budget, owner__isnull=True).count() == 1
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiDetail:
#     """Tests for detail view on TransferCategoryViewSet."""
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_get_category_details(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called by User belonging to Budget.
#         THEN: HTTP 200, TransferCategory details returned.
#         """
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user)
#         else:
#             budget = budget_factory(members=[base_user])
#         category = transfer_category_factory(group__budget=budget)
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.get(url)
#         serializer = TransferCategorySerializer(category)
#
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data == serializer.data
#
#     def test_error_get_category_details_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, transfer_category_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         category = transfer_category_factory()
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_get_details_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         category = transfer_category_factory(group__budget=budget_factory())
#         api_client.force_authenticate(base_user)
#
#         url = category_detail_url(category.group.budget.id, category.id)
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiPartialUpdate:
#     """Tests for partial update view on TransferCategoryViewSet."""
#
#     PAYLOAD = {'name': 'Expenses for food', 'description': 'All money spent for food.', 'is_active': True}
#
#     @pytest.mark.parametrize(
#         'param, value',
#         [
#             ('name', 'New name'),
#             ('description', 'New description'),
#             ('is_active', False),
#         ],
#     )
#     @pytest.mark.django_db
#     def test_category_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, TransferCategory updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget, owner=None, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         assert getattr(category, param) == update_payload[param]
#         assert category.owner is None
#
#     def test_category_partial_update_group(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database. Update payload with "group" value prepared.
#         WHEN: TransferCategorySet detail view called with PATCH by User belonging to Budget with valid payload.
#         THEN: HTTP 200, Deposit updated with "group" value.
#         """
#         member = user_factory()
#         budget = budget_factory(owner=base_user, members=[member])
#         category = transfer_category_factory(group__budget=budget, owner=None, **self.PAYLOAD)
#         new_group = transfer_category_group_factory(budget=budget)
#         update_payload = {'group': new_group.id}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         assert category.group == new_group
#
#     def test_category_partial_update_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database. Update payload with "owner" value prepared.
#         WHEN: TransferCategorySet detail view called with PATCH by User belonging to Budget with valid payload.
#         THEN: HTTP 200, Deposit updated with "owner" value.
#         """
#         member = user_factory()
#         budget = budget_factory(owner=base_user, members=[member])
#         category = transfer_category_factory(group__budget=budget, owner=None, **self.PAYLOAD)
#         update_payload = {'owner': member.id}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         assert category.owner == member
#
#     def test_error_partial_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, transfer_category_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         category = transfer_category_factory()
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_partial_update_category_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PATCH by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         category = transfer_category_factory(group__budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_error_partial_update_group_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup and two Budget instances created in database. TransferCategoryGroup from outer
#         Budget in payload.
#         WHEN: TransferCategoryViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         outer_group = transfer_category_group_factory()
#         payload = {'group': outer_group.id}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'TransferCategoryGroup does not belong to Budget.'
#
#     def test_error_partial_update_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup for Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: TransferCategoryViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         payload = {'owner': user_factory().id}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#
#     def test_error_partial_update_personal_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         in payload.
#         WHEN: TransferCategoryViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(group__budget=budget, owner=base_user, **self.PAYLOAD)
#         category = transfer_category_factory(group__budget=budget, owner=base_user)
#         payload = {'name': self.PAYLOAD['name']}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal TransferCategory with given name already exists in Budget for provided owner.'
#         )
#
#     def test_error_partial_update_common_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         and owner of existing TransferCategory in payload.
#         WHEN: TransferCategoryViewSet called with PATCH by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(group__budget=budget, owner=None, **self.PAYLOAD)
#         category = transfer_category_factory(group__budget=budget, owner=None)
#         payload = {'name': self.PAYLOAD['name']}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.patch(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0] == 'Common TransferCategory with given
#             name already exists in Budget.'
#         )
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiFullUpdate:
#     """Tests for full update view on TransferCategoryViewSet."""
#
#     INITIAL_PAYLOAD = {'name': 'Expenses for food', 'description': 'All money spent for food.', 'is_active': True}
#
#     UPDATE_PAYLOAD = {'name': 'Expenses for clothes', 'description': 'All money spent
#     for clothes.', 'is_active': False}
#
#     @pytest.mark.django_db
#     def test_category_full_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PUT by User belonging to Budget.
#         THEN: HTTP 200, TransferCategory updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget, owner=None, **self.INITIAL_PAYLOAD)
#         new_group = transfer_category_group_factory(budget=budget)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload['group'] = new_group.id
#         update_payload['owner'] = base_user.id
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         for param in update_payload:
#             if param == 'group':
#                 assert getattr(category, param) == new_group
#                 continue
#             elif param == 'owner':
#                 assert getattr(category, param) == base_user
#                 continue
#             assert getattr(category, param) == update_payload[param]
#
#     def test_error_full_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, transfer_category_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         category = transfer_category_factory()
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_full_update_category_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PUT by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         category = transfer_category_factory(group__budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_error_full_update_group_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_group_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup and two Budget instances created in database. TransferCategoryGroup from outer
#         Budget in payload.
#         WHEN: TransferCategoryViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         outer_group = transfer_category_group_factory()
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['group'] = outer_group.id
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'TransferCategoryGroup does not belong to Budget.'
#
#     def test_error_full_update_owner_does_not_belong_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup for Budget instance created in database. User not belonging to Budget as
#         'owner' in payload.
#         WHEN: TransferCategoryViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['group'] = category.group.id
#         payload['owner'] = user_factory().id
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert response.data['non_field_errors'][0] == 'Provided owner does not belong to Budget.'
#
#     def test_error_full_update_personal_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         in payload.
#         WHEN: TransferCategoryViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(group__budget=budget, owner=base_user, **self.INITIAL_PAYLOAD)
#         category = transfer_category_factory(group__budget=budget, owner=base_user)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['group'] = category.group.id
#         payload['name'] = self.INITIAL_PAYLOAD['name']
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0]
#             == 'Personal TransferCategory with given name already exists in Budget for provided owner.'
#         )
#
#     def test_error_full_update_common_category_name_already_used(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance with owner created in database. Name of existing personal TransferCategory
#         and owner of existing TransferCategory in payload.
#         WHEN: TransferCategoryViewSet called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(group__budget=budget, owner=None, **self.INITIAL_PAYLOAD)
#         category = transfer_category_factory(group__budget=budget, owner=None)
#         payload = self.UPDATE_PAYLOAD.copy()
#         payload['group'] = category.group.id
#         payload['name'] = self.INITIAL_PAYLOAD['name']
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.put(url, payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'non_field_errors' in response.data
#         assert (
#             response.data['non_field_errors'][0] == 'Common TransferCategory with
#             given name already exists in Budget.'
#         )
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiDelete:
#     """Tests for delete TransferCategory on TransferCategoryViewSet."""
#
#     def test_delete_category(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, TransferCategory deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(group__budget=budget)
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         assert TransferCategory.objects.filter(group__budget=budget).count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not TransferCategory.objects.filter(group__budget=budget).exists()
#
#     def test_error_delete_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, transfer_category_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         category = transfer_category_factory()
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_delete_category_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         category = transfer_category_factory(group__budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.group.budget.id, category.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
