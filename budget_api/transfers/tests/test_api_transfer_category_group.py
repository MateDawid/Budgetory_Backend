import pytest
from budgets.models import Budget
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient
from transfers.models.transfer_category_group_model import TransferCategoryGroup
from transfers.serializers.transfer_category_group_serializer import (
    TransferCategoryGroupSerializer,
)


def category_group_url(budget_id):
    """Create and return a TransferCategoryGroup detail URL."""
    return reverse('budgets:category_group-list', args=[budget_id])


def category_group_detail_url(budget_id, category_group_id):
    """Create and return a TransferCategoryGroup detail URL."""
    return reverse('budgets:category_group-detail', args=[budget_id, category_group_id])


@pytest.mark.django_db
class TestTransferCategoryGroupApiAccess:
    """Tests for access to TransferCategoryGroupViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryGroupViewSet called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(category_group_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryGroupViewSet called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(category_group_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


@pytest.mark.django_db
class TestTransferCategoryGroupApiList:
    """Tests for list view on TransferCategoryGroupViewSet."""

    def test_retrieve_deposits_list_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        transfer_category_group_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two TransferCategoryGroup model instances for single Budget created in database.
        WHEN: TransferCategoryGroupViewSet called by Budget owner.
        THEN: Response with serialized Budget TransferCategoryGroup list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            transfer_category_group_factory(budget=budget)

        response = api_client.get(category_group_url(budget.id))

        category_groups = TransferCategoryGroup.objects.filter(budget=budget)
        serializer = TransferCategoryGroupSerializer(category_groups, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data


#
#     def test_retrieve_deposits_list_by_member(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two TransferCategoryGroup model instances for single Budget created in database.
#         WHEN: TransferCategoryGroupViewSet called by Budget member.
#         THEN: Response with serialized Budget TransferCategoryGroup list returned.
#         """
#         budget = budget_factory(members=[base_user])
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             deposit_factory(budget=budget)
#
#         response = api_client.get(deposit_url(budget.id))
#
#         deposits = TransferCategoryGroup.objects.filter(budget=budget)
#         serializer = TransferCategoryGroupSerializer(deposits, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_deposits_list_limited_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Two TransferCategoryGroup model instances for different Budgets created in database.
#         WHEN: TransferCategoryGroupViewSet called by one of Budgets owner.
#         THEN: Response with serialized TransferCategoryGroup list (only from given Budget) returned.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget)
#         deposit_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(deposit_url(budget.id))
#
#         deposits = TransferCategoryGroup.objects.filter(budget=budget)
#         serializer = TransferCategoryGroupSerializer(deposits, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert len(response.data['results']) == len(serializer.data) == deposits.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == deposit.id
#
#
# @pytest.mark.django_db
# class TestTransferCategoryGroupApiCreate:
#     """Tests for create TransferCategoryGroup on TransferCategoryGroupViewSet."""
#
#     PAYLOAD = {
#         'name': 'TransferCategoryGroup name',
#         'description': 'TransferCategoryGroup description',
#         'deposit_type': TransferCategoryGroup.TransferCategoryGroupTypes.PERSONAL,
#         'is_active': True,
#     }
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     @pytest.mark.parametrize('with_owner', [True, False])
#     def test_create_single_deposit(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         user_type: str,
#         with_owner: bool,
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload prepared for TransferCategoryGroup.
#         WHEN: TransferCategoryGroupViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: TransferCategoryGroup object created in database with given payload
#         """
#         other_user = user_factory()
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user, members=[other_user])
#         else:
#             budget = budget_factory(members=[base_user, other_user])
#         payload = self.PAYLOAD.copy()
#         if with_owner:
#             payload['owner'] = other_user.id
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(deposit_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert TransferCategoryGroup.objects.filter(budget=budget).count() == 1
#         deposit = TransferCategoryGroup.objects.get(id=response.data['id'])
#         assert deposit.budget == budget
#         if with_owner:
#             assert deposit.owner.id == payload['owner']
#         else:
#             assert deposit.owner is None
#         for key in payload:
#             if key == 'owner':
#                 continue
#             assert getattr(deposit, key) == payload[key]
#         serializer = TransferCategoryGroupSerializer(deposit)
#         assert response.data == serializer.data
#
#     def test_create_two_deposits_for_single_budget(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payloads prepared for two TransferCategoryGroups.
#         WHEN: TransferCategoryGroupViewSet called twice with POST by User belonging to Budget with valid payloads.
#         THEN: Two TransferCategoryGroup objects created in database with given payloads.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload_1 = self.PAYLOAD.copy()
#         payload_1['name'] = 'TransferCategoryGroup name 1'
#         payload_2 = self.PAYLOAD.copy()
#         payload_2['name'] = 'TransferCategoryGroup name 2'
#
#         response_1 = api_client.post(deposit_url(budget.id), payload_1)
#         response_2 = api_client.post(deposit_url(budget.id), payload_2)
#
#         assert response_1.status_code == status.HTTP_201_CREATED
#         assert response_2.status_code == status.HTTP_201_CREATED
#         assert TransferCategoryGroup.objects.filter(budget=budget).count() == 2
#         for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
#             deposit = TransferCategoryGroup.objects.get(id=response.data['id'])
#             for key in payload:
#                 assert getattr(deposit, key) == payload[key]
#
#     def test_create_same_deposit_for_two_budgets(self, api_client: APIClient, budget_factory: FactoryMetaClass):
#         """
#         GIVEN: Two Budget instances created in database. Valid payload prepared for two TransferCategoryGroups.
#         WHEN: TransferCategoryGroupViewSet called twice with POST by different Users belonging to two different
#         Budgets with valid payload.
#         THEN: Two TransferCategoryGroup objects created in database with given payload for separate Budgets.
#         """
#         payload = self.PAYLOAD.copy()
#         budget_1 = budget_factory()
#         budget_2 = budget_factory()
#
#         api_client.force_authenticate(budget_1.owner)
#         api_client.post(deposit_url(budget_1.id), payload)
#         api_client.force_authenticate(budget_2.owner)
#         api_client.post(deposit_url(budget_2.id), payload)
#
#         assert TransferCategoryGroup.objects.all().count() == 2
#         assert TransferCategoryGroup.objects.filter(budget=budget_1).count() == 1
#         assert TransferCategoryGroup.objects.filter(budget=budget_2).count() == 1
#
#     @pytest.mark.parametrize('field_name', ['name', 'description'])
#     def test_error_value_too_long(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
#     ):
#         """
#         GIVEN: Budget instance created in database. Payload for TransferCategoryGroup with field value too long.
#         WHEN: TransferCategoryGroupViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategoryGroup not created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         max_length = TransferCategoryGroup._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload[field_name] = (max_length + 1) * 'a'
#
#         response = api_client.post(deposit_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert field_name in response.data
#         assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
#         assert not TransferCategoryGroup.objects.filter(budget=budget).exists()
#
#     def test_error_name_already_used(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for TransferCategoryGroup.
#         WHEN: TransferCategoryGroupViewSet called twice with POST by User belonging to Budget with the same payload.
#         THEN: Bad request HTTP 400 returned. Only one TransferCategoryGroup created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload = self.PAYLOAD.copy()
#
#         api_client.post(deposit_url(budget.id), payload)
#         response = api_client.post(deposit_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'name' in response.data
#         assert response.data['name'][0] == 'TransferCategoryGroup with given name already exists in Budget.'
#         assert TransferCategoryGroup.objects.filter(budget=budget).count() == 1
#
#     def test_is_active_default_value(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for TransferCategoryGroup.
#         WHEN: TransferCategoryGroupViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: Created HTTP 201 returned. Object created in database with default value for 'is_active' field.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload = self.PAYLOAD.copy()
#         del payload['is_active']
#         default_value = TransferCategoryGroup._meta.get_field('is_active').default
#
#         response = api_client.post(deposit_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert TransferCategoryGroup.objects.all().count() == 1
#         assert TransferCategoryGroup.objects.filter(budget=budget).count() == 1
#         assert response.data['is_active'] == default_value
#
#     def test_error_create_deposit_for_not_accessible_budget(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for TransferCategoryGroup.
#         WHEN: TransferCategoryGroupViewSet called with POST by User not belonging to Budget with valid payload.
#         THEN: Forbidden HTTP 403 returned. Object not created.
#         """
#         budget = budget_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(deposit_url(budget.id), self.PAYLOAD)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#         assert not TransferCategoryGroup.objects.filter(budget=budget).exists()
#
#
# @pytest.mark.django_db
# class TestTransferCategoryGroupApiDetail:
#     """Tests for detail view on TransferCategoryGroupViewSet."""
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_get_deposit_details(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called by User belonging to Budget.
#         THEN: HTTP 200, TransferCategoryGroup details returned.
#         """
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user)
#         else:
#             budget = budget_factory(members=[base_user])
#         deposit = deposit_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.get(url)
#         serializer = TransferCategoryGroupSerializer(deposit)
#
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data == serializer.data
#
#     def test_error_get_deposit_details_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         deposit = deposit_factory()
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
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
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         deposit = deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#         response = api_client.get(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#
# @pytest.mark.django_db
# class TestTransferCategoryGroupApiPartialUpdate:
#     """Tests for partial update view on TransferCategoryGroupViewSet."""
#
#     PAYLOAD = {
#         'name': 'TransferCategoryGroup name',
#         'description': 'TransferCategoryGroup description',
#         'deposit_type': TransferCategoryGroup.TransferCategoryGroupTypes.PERSONAL,
#         'is_active': True,
#         'owner': None,
#     }
#
#     @pytest.mark.parametrize(
#         'param, value', [('name', 'New name'), ('description', 'New description'), ('is_active', False)]
#     )
#     @pytest.mark.django_db
#     def test_deposit_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, TransferCategoryGroup updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         assert getattr(deposit, param) == update_payload[param]
#
#     def test_error_partial_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         deposit = deposit_factory()
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_partial_update_deposit_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         deposit = deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_deposit_partial_update_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         Update payload with "owner" value prepared.
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH by
#         User belonging to Budget with valid payload.
#         THEN: HTTP 200, TransferCategoryGroup updated with "owner" value.
#         """
#         member = user_factory()
#         budget = budget_factory(owner=base_user, members=[member])
#         deposit = deposit_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {'owner': member.id}
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         assert deposit.owner == member
#
#     @pytest.mark.parametrize('param, value', [('name', PAYLOAD['name']), ('deposit_type', 5)])
#     def test_error_on_deposit_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database. Update payload with invalid value.
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH by
#         User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategoryGroup not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit_factory(budget=budget, **self.PAYLOAD)
#         deposit = deposit_factory(budget=budget)
#         old_value = getattr(deposit, param)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         assert getattr(deposit, param) == old_value
#
#     def test_error_on_deposit_partial_update_with_owner_not_belonging_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database. Update payload with User not
#         belonging to budget as "owner".
#         WHEN: TransferCategoryGroupViewSet detail view called with PATCH by
#         User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategoryGroup not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget, owner=None)
#         update_payload = {'owner': user_factory()}
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         assert deposit.owner is None
#
#
# @pytest.mark.django_db
# class TestTransferCategoryGroupApiFullUpdate:
#     """Tests for full update view on TransferCategoryGroupViewSet."""
#
#     INITIAL_PAYLOAD = {
#         'name': 'TransferCategoryGroup name',
#         'description': 'TransferCategoryGroup description',
#         'deposit_type': TransferCategoryGroup.TransferCategoryGroupTypes.PERSONAL,
#         'is_active': True,
#     }
#
#     UPDATE_PAYLOAD = {
#         'name': 'Updated name',
#         'description': 'Updated description',
#         'deposit_type': TransferCategoryGroup.TransferCategoryGroupTypes.COMMON,
#         'is_active': False,
#     }
#
#     @pytest.mark.django_db
#     def test_deposit_full_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT by User belonging to Budget.
#         THEN: HTTP 200, TransferCategoryGroup updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.put(url, self.UPDATE_PAYLOAD)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         for param in self.UPDATE_PAYLOAD:
#             assert getattr(deposit, param) == self.UPDATE_PAYLOAD[param]
#
#     def test_error_full_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         deposit = deposit_factory()
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_full_update_deposit_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         deposit = deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     def test_deposit_full_update_owner(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         Update payload with "owner" value prepared.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT by User belonging to Budget with valid payload.
#         THEN: HTTP 200, TransferCategoryGroup updated with "owner" value.
#         """
#         member = user_factory()
#         budget = budget_factory(owner=base_user, members=[member])
#         deposit = deposit_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload['owner'] = member.id
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         deposit.refresh_from_db()
#         assert deposit.owner == member
#         for param in update_payload:
#             if param == 'owner':
#                 continue
#             assert getattr(deposit, param) == update_payload[param]
#
#     @pytest.mark.parametrize('param, value', [('name', INITIAL_PAYLOAD['name']), ('deposit_type', 5)])
#     def test_error_on_deposit_full_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database. Update payload with invalid value.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT by User
#         belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategoryGroup not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         deposit = deposit_factory(budget=budget)
#         old_value = getattr(deposit, param)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload[param] = value
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         assert getattr(deposit, param) == old_value
#
#     def test_error_on_deposit_full_update_with_owner_not_belonging_to_budget(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database. Update payload with User not
#         belonging to budget as "owner".
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT by User
#         belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategoryGroup not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget, owner=None, **self.INITIAL_PAYLOAD)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload['owner'] = user_factory()
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         deposit.refresh_from_db()
#         assert deposit.owner is None
#
#
# @pytest.mark.django_db
# class TestTransferCategoryGroupApiDelete:
#     """Tests for delete TransferCategoryGroup on TransferCategoryGroupViewSet."""
#
#     def test_delete_deposit(
#         self, api_client: APIClient, base_user: Any, budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, TransferCategoryGroup deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         deposit = deposit_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(budget.id, deposit.id)
#
#         assert budget.deposits.all().exists() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not budget.deposits.all().exists()
#
#     def test_error_delete_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, deposit_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         deposit = deposit_factory()
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_delete_deposit_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         deposit_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategoryGroup instance for Budget created in database.
#         WHEN: TransferCategoryGroupViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         deposit = deposit_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = deposit_detail_url(deposit.budget.id, deposit.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
