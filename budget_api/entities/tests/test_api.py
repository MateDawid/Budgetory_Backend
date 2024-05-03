import pytest
from budgets.models import Budget
from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from entities.models import Entity
from entities.serializers import EntitySerializer
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.test import APIClient


def entities_url(budget_id):
    """Create and return a Entity detail URL."""
    return reverse('budgets:entity-list', args=[budget_id])


def entity_detail_url(budget_id, entity_id):
    """Create and return a Entity detail URL."""
    return reverse('budgets:entity-detail', args=[budget_id, entity_id])


@pytest.mark.django_db
class TestEntityApiAccess:
    """Tests for access to EntityViewSet."""

    def test_auth_required(self, api_client: APIClient, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: EntityViewSet called without authentication.
        THEN: Unauthorized HTTP 401 returned.
        """
        res = api_client.get(entities_url(budget.id))

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_not_budget_member(
        self, api_client: APIClient, user_factory: FactoryMetaClass, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget model instance in database.
        WHEN: EntityViewSet called by User not belonging to given Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        budget_owner = user_factory()
        other_user = user_factory()
        budget = budget_factory(owner=budget_owner)
        api_client.force_authenticate(other_user)

        response = api_client.get(entities_url(budget.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


@pytest.mark.django_db
class TestEntityApiList:
    """Tests for list view on EntityViewSet."""

    def test_retrieve_entity_list_by_owner(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Entity model instances for single Budget created in database.
        WHEN: EntityViewSet called by Budget owner.
        THEN: Response with serialized Budget Entity list returned.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        for _ in range(2):
            entity_factory(budget=budget)

        response = api_client.get(entities_url(budget.id))

        entities = Entity.objects.filter(budget=budget)
        serializer = EntitySerializer(entities, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_retrieve_entities_list_by_member(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Entity model instances for single Budget created in database.
        WHEN: EntityViewSet called by Budget member.
        THEN: Response with serialized Budget Entity list returned.
        """
        budget = budget_factory(members=[base_user])
        api_client.force_authenticate(base_user)
        for _ in range(2):
            entity_factory(budget=budget)

        response = api_client.get(entities_url(budget.id))

        entities = Entity.objects.filter(budget=budget)
        serializer = EntitySerializer(entities, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_entities_list_limited_to_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two Entity model instances for different Budgets created in database.
        WHEN: EntityViewSet called by one of Budgets owner.
        THEN: Response with serialized Entity list (only from given Budget) returned.
        """
        budget = budget_factory(owner=base_user)
        entity = entity_factory(budget=budget)
        entity_factory()
        api_client.force_authenticate(base_user)

        response = api_client.get(entities_url(budget.id))

        entities = Entity.objects.filter(budget=budget)
        serializer = EntitySerializer(entities, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == len(serializer.data) == entities.count() == 1
        assert response.data['results'] == serializer.data
        assert response.data['results'][0]['id'] == entity.id


@pytest.mark.django_db
class TestEntityApiCreate:
    """Tests for create Entity on EntityViewSet."""

    PAYLOAD = {
        'name': 'Supermarket',
        'description': 'Supermarket in which I buy food.',
    }

    @pytest.mark.parametrize('user_type', ['owner', 'member'])
    def test_create_single_entity(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        user_factory: FactoryMetaClass,
        budget_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: Budget instance created in database. Valid payload prepared for Entity.
        WHEN: EntityViewSet called with POST by User belonging to Budget with valid payload.
        THEN: Entity object created in database with given payload
        """
        other_user = user_factory()
        if user_type == 'owner':
            budget = budget_factory(owner=base_user, members=[other_user])
        else:
            budget = budget_factory(members=[base_user, other_user])
        api_client.force_authenticate(base_user)

        response = api_client.post(entities_url(budget.id), self.PAYLOAD)

        assert response.status_code == status.HTTP_201_CREATED
        assert Entity.objects.filter(budget=budget).count() == 1
        entity = Entity.objects.get(id=response.data['id'])
        assert entity.budget == budget
        for key in self.PAYLOAD:
            assert getattr(entity, key) == self.PAYLOAD[key]
        serializer = EntitySerializer(entity)
        assert response.data == serializer.data

    def test_create_two_entities_for_single_budget(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payloads prepared for two entities.
        WHEN: EntityViewSet called twice with POST by User belonging to Budget with valid payloads.
        THEN: Two Entity objects created in database with given payloads.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload_1 = self.PAYLOAD.copy()
        payload_1['name'] = 'Entity name 1'
        payload_2 = self.PAYLOAD.copy()
        payload_2['name'] = 'Entity name 2'

        response_1 = api_client.post(entities_url(budget.id), payload_1)
        response_2 = api_client.post(entities_url(budget.id), payload_2)

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED
        assert Entity.objects.filter(budget=budget).count() == 2
        for response, payload in [(response_1, payload_1), (response_2, payload_2)]:
            entity = Entity.objects.get(id=response.data['id'])
            for key in payload:
                assert getattr(entity, key) == payload[key]

    def test_create_same_entity_for_two_budgets(self, api_client: APIClient, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget instances created in database. Valid payload prepared for two entities.
        WHEN: EntityViewSet called twice with POST by different Users belonging to two different
        Budgets with valid payload.
        THEN: Two Entity objects created in database with given payload for separate Budgets.
        """
        payload = self.PAYLOAD.copy()
        budget_1 = budget_factory()
        budget_2 = budget_factory()

        api_client.force_authenticate(budget_1.owner)
        api_client.post(entities_url(budget_1.id), payload)
        api_client.force_authenticate(budget_2.owner)
        api_client.post(entities_url(budget_2.id), payload)

        assert Entity.objects.all().count() == 2
        assert Entity.objects.filter(budget=budget_1).count() == 1
        assert Entity.objects.filter(budget=budget_2).count() == 1

    @pytest.mark.parametrize('field_name', ['name', 'description'])
    def test_error_value_too_long(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass, field_name: str
    ):
        """
        GIVEN: Budget instance created in database. Payload for Entity with field value too long.
        WHEN: EntityViewSet called with POST by User belonging to Budget with invalid payload.
        THEN: Bad request HTTP 400 returned. Entity not created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        max_length = Entity._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * 'a'

        response = api_client.post(entities_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert field_name in response.data
        assert response.data[field_name][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not Entity.objects.filter(budget=budget).exists()

    def test_error_name_already_used(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Entity.
        WHEN: EntityViewSet called twice with POST by User belonging to Budget with the same payload.
        THEN: Bad request HTTP 400 returned. Only one Entity created in database.
        """
        budget = budget_factory(owner=base_user)
        api_client.force_authenticate(base_user)
        payload = self.PAYLOAD.copy()

        api_client.post(entities_url(budget.id), payload)
        response = api_client.post(entities_url(budget.id), payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == 'Entity with given name already exists in Budget.'
        assert Entity.objects.filter(budget=budget).count() == 1

    def test_error_create_entity_for_not_accessible_budget(
        self, api_client: APIClient, base_user: AbstractUser, budget_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget instance created in database. Valid payload for Entity.
        WHEN: EntityViewSet called with POST by User not belonging to Budget with valid payload.
        THEN: Forbidden HTTP 403 returned. Object not created.
        """
        budget = budget_factory()
        api_client.force_authenticate(base_user)

        response = api_client.post(entities_url(budget.id), self.PAYLOAD)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'
        assert not Entity.objects.filter(budget=budget).exists()


@pytest.mark.django_db
class TestEntityApiDetail:
    """Tests for detail view on EntityViewSet."""

    @pytest.mark.parametrize('user_type', ['owner', 'member'])
    def test_get_entity_details(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        user_type: str,
    ):
        """
        GIVEN: Entity instance for Budget created in database.
        WHEN: EntityViewSet detail view called by User belonging to Budget.
        THEN: HTTP 200, Entity details returned.
        """
        if user_type == 'owner':
            budget = budget_factory(owner=base_user)
        else:
            budget = budget_factory(members=[base_user])
        entity = entity_factory(budget=budget)
        api_client.force_authenticate(base_user)
        url = entity_detail_url(budget.id, entity.id)

        response = api_client.get(url)
        serializer = EntitySerializer(entity)

        assert response.status_code == status.HTTP_200_OK
        assert response.data == serializer.data

    def test_error_get_entity_details_unauthenticated(
        self, api_client: APIClient, base_user: AbstractUser, entity_factory: FactoryMetaClass
    ):
        """
        GIVEN: Entity instance for Budget created in database.
        WHEN: EntityViewSet detail view called without authentication.
        THEN: Unauthorized HTTP 401.
        """
        entity = entity_factory()
        url = entity_detail_url(entity.budget.id, entity.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_details_from_not_accessible_budget(
        self,
        api_client: APIClient,
        base_user: AbstractUser,
        budget_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Entity instance for Budget created in database.
        WHEN: EntityViewSet detail view called by User not belonging to Budget.
        THEN: Forbidden HTTP 403 returned.
        """
        entity = entity_factory(budget=budget_factory())
        api_client.force_authenticate(base_user)

        url = entity_detail_url(entity.budget.id, entity.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'User does not have access to Budget.'


# @pytest.mark.django_db
# class TestEntityApiPartialUpdate:
#     """Tests for partial update view on EntityViewSet."""
#
#     PAYLOAD = {
#         'name': 'Most important expenses',
#         'description': 'Category for most important expenses.',
#         'transfer_type': Entity.TransferTypes.EXPENSE,
#     }
#
#     @pytest.mark.parametrize(
#         'param, value',
#         [
#             ('name', 'New name'),
#             ('description', 'New description'),
#             ('transfer_type', Entity.TransferTypes.INCOME),
#         ],
#     )
#     @pytest.mark.django_db
#     def test_entity_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PATCH by User belonging to Budget.
#         THEN: HTTP 200, Entity updated.
#         """
#         budget = budget_factory(owner=base_user)
#         entity = entity_factory(budget=budget, **self.PAYLOAD)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(budget.id, entity.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_200_OK
#         entity.refresh_from_db()
#         assert getattr(entity, param) == update_payload[param]
#
#     def test_error_partial_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, entity_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PATCH without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         entity = entity_factory()
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_partial_update_entity_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PATCH by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         entity = entity_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.patch(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     @pytest.mark.parametrize('param, value', [('name', PAYLOAD['name']), ('transfer_type', 999)])
#     def test_error_on_entity_partial_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database. Update payload with invalid value.
#         WHEN: EntityViewSet detail view called with PATCH by User belonging to Budget
#         with invalid payload.
#         THEN: Bad request HTTP 400, Entity not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         entity_factory(budget=budget, **self.PAYLOAD)
#         entity = entity_factory(budget=budget)
#         old_value = getattr(entity, param)
#         update_payload = {param: value}
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(budget.id, entity.id)
#
#         response = api_client.patch(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         entity.refresh_from_db()
#         assert getattr(entity, param) == old_value
#
#
# @pytest.mark.django_db
# class TestEntityApiFullUpdate:
#     """Tests for full update view on EntityViewSet."""
#
#     INITIAL_PAYLOAD = {
#         'name': 'Most important expenses',
#         'description': 'Category for most important expenses.',
#         'transfer_type': Entity.TransferTypes.EXPENSE,
#     }
#
#     UPDATE_PAYLOAD = {
#         'name': 'Updated name',
#         'description': 'Updated description',
#         'transfer_type': Entity.TransferTypes.INCOME,
#     }
#
#     @pytest.mark.django_db
#     def test_entity_full_update(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PUT by User belonging to Budget.
#         THEN: HTTP 200, Entity updated.
#         """
#         budget = budget_factory(owner=base_user)
#         entity = entity_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(budget.id, entity.id)
#
#         response = api_client.put(url, self.UPDATE_PAYLOAD)
#
#         assert response.status_code == status.HTTP_200_OK
#         entity.refresh_from_db()
#         for param in self.UPDATE_PAYLOAD:
#             assert getattr(entity, param) == self.UPDATE_PAYLOAD[param]
#
#     def test_error_full_update_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, entity_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         entity = entity_factory()
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_full_update_entity_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PUT by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         entity = entity_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.put(url, {})
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
#
#     @pytest.mark.parametrize('param, value', [('name', INITIAL_PAYLOAD['name']), ('transfer_type', 999)])
#     def test_error_on_entity_full_update(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#         param: str,
#         value: Any,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database. Update payload with invalid value.
#         WHEN: EntityViewSet detail view called with PUT by User belonging to Budget with invalid payload.
#         THEN: Bad request HTTP 400, Entity not updated.
#         """
#         budget = budget_factory(owner=base_user)
#         entity_factory(budget=budget, **self.INITIAL_PAYLOAD)
#         entity = entity_factory(budget=budget)
#         old_value = getattr(entity, param)
#         update_payload = self.UPDATE_PAYLOAD.copy()
#         update_payload[param] = value
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(budget.id, entity.id)
#
#         response = api_client.put(url, update_payload)
#
#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         entity.refresh_from_db()
#         assert getattr(entity, param) == old_value
#
#
# @pytest.mark.django_db
# class TestEntityApiDelete:
#     """Tests for delete Entity on EntityViewSet."""
#
#     def test_delete_entity(
#         self,
#         api_client: APIClient,
#         base_user: Any,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with DELETE by User belonging to Budget.
#         THEN: No content HTTP 204, Entity deleted.
#         """
#         budget = budget_factory(owner=base_user)
#         entity = entity_factory(budget=budget)
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(budget.id, entity.id)
#
#         assert budget.entities.all().count() == 1
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_204_NO_CONTENT
#         assert not budget.entities.all().exists()
#
#     def test_error_delete_unauthenticated(
#         self, api_client: APIClient, base_user: AbstractUser, entity_factory: FactoryMetaClass
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with PUT without authentication.
#         THEN: Unauthorized HTTP 401.
#         """
#         entity = entity_factory()
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
#
#     def test_error_delete_entity_from_not_accessible_budget(
#         self,
#         api_client: APIClient,
#         base_user: AbstractUser,
#         budget_factory: FactoryMetaClass,
#         entity_factory: FactoryMetaClass,
#     ):
#         """
#         GIVEN: Entity instance for Budget created in database.
#         WHEN: EntityViewSet detail view called with DELETE by User not belonging to Budget.
#         THEN: Forbidden HTTP 403 returned.
#         """
#         entity = entity_factory(budget=budget_factory())
#         api_client.force_authenticate(base_user)
#         url = entity_detail_url(entity.budget.id, entity.id)
#
#         response = api_client.delete(url)
#
#         assert response.status_code == status.HTTP_403_FORBIDDEN
#         assert response.data['detail'] == 'User does not have access to Budget.'
