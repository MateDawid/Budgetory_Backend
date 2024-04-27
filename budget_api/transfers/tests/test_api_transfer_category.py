import pytest
from budgets.models import Budget
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient


def category_url(budget_id):
    """Create and return a TransferCategory detail URL."""
    return reverse('budgets:category-list', args=[budget_id])


def category_detail_url(budget_id, category_id):
    """Create and return a TransferCategory detail URL."""
    return reverse('budgets:category-detail', args=[budget_id, category_id])


@pytest.mark.django_db
class TestTransferCategoryApiAccess:
    """Tests for access to TransferCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(category_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategoryViewSet called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(category_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


# @pytest.mark.django_db
# class TestTransferCategoryApiList:
#     """Tests for list view on TransferCategoryViewSet."""
#
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
#         for _ in range(2):
#             transfer_category_factory(group__budget=budget)
#         api_client.force_authenticate(base_user)
#         for _ in range(2):
#             transfer_category_factory(budget=budget)
#
#         response = api_client.get(category_url(budget.id))
#
#         categorys = TransferCategory.objects.filter(budget=budget)
#         serializer = TransferCategorySerializer(categorys, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data

#     def test_retrieve_categorys_list_by_member(
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
#             transfer_category_factory(budget=budget)
#
#         response = api_client.get(category_url(budget.id))
#
#         categorys = TransferCategory.objects.filter(budget=budget)
#         serializer = TransferCategorySerializer(categorys, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert response.data['results'] == serializer.data
#
#     def test_categorys_list_limited_to_budget(
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
#         category = transfer_category_factory(budget=budget)
#         transfer_category_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.get(category_url(budget.id))
#
#         categorys = TransferCategory.objects.filter(budget=budget)
#         serializer = TransferCategorySerializer(categorys, many=True)
#         assert response.status_code == status.HTTP_200_OK
#         assert len(response.data['results']) == len(serializer.data) == categorys.count() == 1
#         assert response.data['results'] == serializer.data
#         assert response.data['results'][0]['id'] == category.id
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiCreate:
#     """Tests for create TransferCategory on TransferCategoryViewSet."""
#
#     PAYLOAD = {
#         'name': 'Most important expenses',
#         'description': 'Category for most important expenses.',
#         'transfer_type': TransferCategory.TransferTypes.EXPENSE,
#     }
#
#     @pytest.mark.parametrize('user_type', ['owner', 'member'])
#     def test_create_single_category(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         user_factory: FactoryMetaClass,
#         budget_factory: FactoryMetaClass,
#         user_type: str,
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload prepared for TransferCategory.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with valid payload.
#         THEN: TransferCategory object created in database with given payload
#         """
#         other_user = user_factory()
#         if user_type == 'owner':
#             budget = budget_factory(owner=base_user, members=[other_user])
#         else:
#             budget = budget_factory(members=[base_user, other_user])
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(category_url(budget.id), self.PAYLOAD)
#
#         assert response.status_code == status.HTTP_201_CREATED
#         assert TransferCategory.objects.filter(budget=budget).count() == 1
#         category = TransferCategory.objects.get(id=response.data['id'])
#         assert category.budget == budget
#         for key in self.PAYLOAD:
#             assert getattr(category, key) == self.PAYLOAD[key]
#         serializer = TransferCategorySerializer(category)
#         assert response.data == serializer.data
#
#     def test_create_two_categorys_for_single_budget(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payloads prepared for two TransferCategorys.
#         WHEN: TransferCategoryViewSet called twice with POST by User belonging to Budget with valid payloads.
#         THEN: Two TransferCategory objects created in database with given payloads.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload_1 = self.PAYLOAD.copy()
#         payload_1['name'] = 'TransferCategory name 1'
#         payload_2 = self.PAYLOAD.copy()
#         payload_2['name'] = 'TransferCategory name 2'
#
#         response_1 = api_client.post(category_url(budget.id), payload_1)
#         response_2 = api_client.post(category_url(budget.id), payload_2)
#
#         assert response_1.status_code == status.HTTP_201_CREATED
#         assert response_2.status_code == status.HTTP_201_CREATED
#         assert TransferCategory.objects.filter(budget=budget).count() == 2
#         for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
#             category = TransferCategory.objects.get(id=response.data['id'])
#             for key in payload:
#                 assert getattr(category, key) == payload[key]
#
#     def test_create_same_category_for_two_budgets(self, api_client: APIClient, budget_factory: FactoryMetaClass):
#         """
#         GIVEN: Two Budget instances created in database. Valid payload prepared for two TransferCategorys.
#         WHEN: TransferCategoryViewSet called twice with POST by different Users belonging to two different
#         Budgets with valid payload.
#         THEN: Two TransferCategory objects created in database with given payload for separate Budgets.
#         """
#         payload = self.PAYLOAD.copy()
#         budget_1 = budget_factory()
#         budget_2 = budget_factory()
#
#         api_client.force_authenticate(budget_1.owner)
#         api_client.post(category_url(budget_1.id), payload)
#         api_client.force_authenticate(budget_2.owner)
#         api_client.post(category_url(budget_2.id), payload)
#
#         assert TransferCategory.objects.all().count() == 2
#         assert TransferCategory.objects.filter(budget=budget_1).count() == 1
#         assert TransferCategory.objects.filter(budget=budget_2).count() == 1
#
#     @pytest.mark.parametrize('field_name', ['name', 'description'])
#     def test_error_value_too_long(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
#     ):
#         """
#         GIVEN: Budget instance created in database. Payload for TransferCategory with field value too long.
#         WHEN: TransferCategoryViewSet called with POST by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400 returned. TransferCategory not created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         max_length = TransferCategory._meta.get_field(field_name).max_length
#         payload = self.PAYLOAD.copy()
#         payload[field_name] = (max_length + 1) * 'a'
#
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert field_name in response.data
#         assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
#         assert not TransferCategory.objects.filter(budget=budget).exists()
#
#     def test_error_name_already_used(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for TransferCategory.
#         WHEN: TransferCategoryViewSet called twice with POST by User belonging to Budget with the same payload.
#         THEN: Bad request HTTP 400 returned. Only one TransferCategory created in database.
#         """
#         budget = budget_factory(owner=base_user)
#         api_client.force_authenticate(base_user)
#         payload = self.PAYLOAD.copy()
#
#         api_client.post(category_url(budget.id), payload)
#         response = api_client.post(category_url(budget.id), payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert 'name' in response.data
#         assert response.data['name'][0] == 'TransferCategory with given name already exists in Budget.'
#         assert TransferCategory.objects.filter(budget=budget).count() == 1
#
#     def test_error_create_category_for_not_accessible_budget(
#         self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Budget instance created in database. Valid payload for TransferCategory.
#         WHEN: TransferCategoryViewSet called with POST by User not belonging to Budget with valid payload.
#         THEN: Forbidden HTTP 403 returned. Object not created.
#         """
#         budget = budget_factory()
#         api_client.force_authenticate(base_user)
#
#         response = api_client.post(category_url(budget.id), self.PAYLOAD)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#         assert not TransferCategory.objects.filter(budget=budget).exists()
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
#         category = transfer_category_factory(budget=budget)
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
#         url = category_detail_url(category.budget.id, category.id)
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
#         category = transfer_category_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#
#         url = category_detail_url(category.budget.id, category.id)
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
#     PAYLOAD = {
#         'name': 'Most important expenses',
#         'description': 'Category for most important expenses.',
#         'transfer_type': TransferCategory.TransferTypes.EXPENSE,
#     }
#
#     @pytest.mark.parametrize(
#         'param, value',
#         [
#             ('name', 'New name'),
#             ('description', 'New description'),
#             ('transfer_type', TransferCategory.TransferTypes.INCOME),
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
#         category = transfer_category_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         assert getattr(category, param) == update_payload[param]
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
#         url = category_detail_url(category.budget.id, category.id)
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
#         category = transfer_category_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.budget.id, category.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     @pytest.mark.parametrize('param, value', [('name', PAYLOAD['name']), ('transfer_type', 999)])
#     def test_error_on_category_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database. Update payload with invalid value.
#         WHEN: TransferCategoryViewSet detail view called with PATCH by User belonging to Budget
#         with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(budget=budget, **self.PAYLOAD)
#         category = transfer_category_factory(budget=budget)
#         old_value = getattr(category, param)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         category.refresh_from_db()
#         assert getattr(category, param) == old_value
#
#
# @pytest.mark.django_db
# class TestTransferCategoryApiFullUpdate:
#     """Tests for full update view on TransferCategoryViewSet."""
#
#     INITIAL_PAYLOAD = {
#         'name': 'Most important expenses',
#         'description': 'Category for most important expenses.',
#         'transfer_type': TransferCategory.TransferTypes.EXPENSE,
#     }
#
#     UPDATE_PAYLOAD = {
#         'name': 'Updated name',
#         'description': 'Updated description',
#         'transfer_type': TransferCategory.TransferTypes.INCOME,
#     }
#
#     @pytest.mark.django_db
#     def test_category_full_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database.
#         WHEN: TransferCategoryViewSet detail view called with PUT by User belonging to Budget.
#         THEN: HTTP 200, TransferCategory updated.
#         """
#         budget = budget_factory(owner=base_user)
#         category = transfer_category_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.put(url, self.UPDATE_PAYLOAD)
#
#         assert response.status_code == status.HTTP_200_OK
#         category.refresh_from_db()
#         for param in self.UPDATE_PAYLOAD:
#             assert getattr(category, param) == self.UPDATE_PAYLOAD[param]
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
#         url = category_detail_url(category.budget.id, category.id)
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
#         category = transfer_category_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.budget.id, category.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     @pytest.mark.parametrize('param, value', [('name', INITIAL_PAYLOAD['name']), ('transfer_type', 999)])
#     def test_error_on_category_full_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         transfer_category_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: TransferCategory instance for Budget created in database. Update payload with invalid value.
#         WHEN: TransferCategoryViewSet detail view called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, TransferCategory not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         transfer_category_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         category = transfer_category_factory(budget=budget)
#         old_value = getattr(category, param)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload[param] = value
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         category.refresh_from_db()
#         assert getattr(category, param) == old_value
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
#         category = transfer_category_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(budget.id, category.id)
#
#         assert budget.categorys.all().exists() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not budget.categorys.all().exists()
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
#         url = category_detail_url(category.budget.id, category.id)
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
#         category = transfer_category_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = category_detail_url(category.budget.id, category.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
