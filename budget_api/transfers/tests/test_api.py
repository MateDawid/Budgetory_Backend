from typing import Any

import pytest
from django.db.models import Q
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status

# from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from transfers.models import TransferCategory
from transfers.serializers import TransferCategorySerializer

TRANSFER_CATEGORIES_URL = reverse('transfers:transfercategory-list')


def transfer_category_detail_url(transfer_category_id):
    """Create and return transfer category detail URL."""
    return reverse('transfers:transfercategory-detail', args=[transfer_category_id])


@pytest.mark.django_db
class TestTransferCategoryApi:
    """Tests for TransferCategoryViewSet."""

    def test_auth_required(self, api_client: APIClient):
        """Test auth is required to call endpoint."""

        res = api_client.get(TRANSFER_CATEGORIES_URL)

        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_transfer_categories_list(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test retrieving list of transfer categories."""
        api_client.force_authenticate(base_user)
        transfer_category_factory(user=None)
        transfer_category_factory(user=base_user)

        response = api_client.get(TRANSFER_CATEGORIES_URL)

        entities = TransferCategory.objects.all()
        serializer = TransferCategorySerializer(entities, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_transfer_category_list_limited_to_user(
        self, api_client: APIClient, user_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """Test retrieved list of transfer categories is limited to personal for authenticated user and global ones."""
        user = user_factory()
        transfer_category_factory(user=user, scope=TransferCategory.PERSONAL)
        transfer_category_factory(user=None, scope=TransferCategory.GLOBAL)
        transfer_category_factory(user=user_factory(), scope=TransferCategory.PERSONAL)
        api_client.force_authenticate(user)

        response = api_client.get(TRANSFER_CATEGORIES_URL)

        entities = TransferCategory.objects.filter(
            Q(scope=TransferCategory.GLOBAL) | Q(scope=TransferCategory.PERSONAL, user=user)
        ).distinct()
        serializer = TransferCategorySerializer(entities, many=True)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'] == serializer.data

    def test_create_personal_transfer_category(self, api_client: APIClient, base_user: Any):
        """Test creating personal TransferCategory."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'user': base_user,
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert base_user.personal_transfer_categories.all().count() == 1
        assert not TransferCategory.global_transfer_categories.all().exists()
        category = TransferCategory.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(category, key) == payload[key]
        serializer = TransferCategorySerializer(category)
        assert response.data == serializer.data
        assert category.user == base_user

    def test_create_global_transfer_category(self, api_client: APIClient, admin_user: Any):
        """Test creating global TransferCategory."""
        api_client.force_authenticate(admin_user)
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert not admin_user.personal_entities.all().exists()
        assert TransferCategory.global_transfer_categories.all().count() == 1
        category = TransferCategory.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(category, key) == payload[key]
        serializer = TransferCategorySerializer(category)
        assert response.data == serializer.data
        assert category.user is None

    # def test_create_global_transfer_category(self, api_client: APIClient, base_user: Any):
    #     """Test error on creating global TransferCategory by non admin user."""
    #
    #     # TODO - apply such logic
    #     pass

    # def test_create_same_personal_entity_by_two_users(self, api_client: APIClient, user_factory: Any):
    #     """Test creating personal entity with the same params by two users."""
    #     payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': Entity.PERSONAL}
    #     user_1 = user_factory()
    #     api_client.force_authenticate(user_1)
    #     api_client.post(ENTITIES_URL, payload)
    #
    #     user_2 = user_factory()
    #     api_client.force_authenticate(user_2)
    #     api_client.post(ENTITIES_URL, payload)
    #
    #     assert Entity.objects.all().count() == 2
    #     assert not Entity.global_entities.all().exists()
    #     assert user_1.personal_entities.all().count() == 1
    #     assert user_2.personal_entities.all().count() == 1
    #
    # def test_error_name_too_long(self, api_client: APIClient, base_user: Any):
    #     """Test error on creating Entity with name too long."""
    #     api_client.force_authenticate(base_user)
    #     max_length = Entity._meta.get_field('name').max_length
    #     payload = {'name': 'A' * (max_length + 1), 'description': 'Selling stuff.', 'type': Entity.GLOBAL}
    #
    #     response = api_client.post(ENTITIES_URL, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     assert 'name' in response.data
    #     assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
    #     assert not Entity.global_entities.all().exists()
    #
    # def test_error_global_name_already_used(self, api_client: APIClient, base_user: Any):
    #     """Test error on creating global Entity with already used name."""
    #     api_client.force_authenticate(base_user)
    #     payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': Entity.GLOBAL}
    #     Entity.objects.create(**payload)
    #
    #     response = api_client.post(ENTITIES_URL, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     assert 'non_field_errors' in response.data
    #     assert response.data['non_field_errors'][0] == 'Global entity with given name already exists.'
    #     assert Entity.global_entities.all().count() == 1
    #
    # def test_error_personal_name_already_used(self, api_client: APIClient, base_user: Any):
    #     """Test error on creating personal Entity with already used name."""
    #     api_client.force_authenticate(base_user)
    #     payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': Entity.PERSONAL}
    #     Entity.objects.create(user=base_user, **payload)
    #
    #     response = api_client.post(ENTITIES_URL, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     assert 'non_field_errors' in response.data
    #     assert response.data['non_field_errors'][0] == 'Personal entity with given name already exists.'
    #     assert base_user.personal_entities.all().count() == 1
    #
    # def test_error_description_too_long(self, api_client: APIClient, base_user: Any):
    #     """Test error on creating Entity with description too long."""
    #     api_client.force_authenticate(base_user)
    #     max_length = Entity._meta.get_field('description').max_length
    #     payload = {'name': 'Seller', 'description': 'A' * (max_length + 1), 'type': Entity.GLOBAL}
    #
    #     response = api_client.post(ENTITIES_URL, payload)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     assert 'description' in response.data
    #     assert response.data['description'][0] == f'Ensure this field has no more than {max_length} characters.'
    #     assert not Entity.global_entities.all().exists()
    #
    # def test_error_on_user_in_global_entity(self, base_user: Any):
    #     """Test error on validating data in EntitySerializer when user was provided for global Entity."""
    #     payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': Entity.GLOBAL, 'user': base_user.pk}
    #
    #     serializer = EntitySerializer(data=payload)
    #     with pytest.raises(ValidationError) as exc:
    #         serializer.is_valid(raise_exception=True)
    #     assert str(exc.value.detail['non_field_errors'][0]) == 'User can be provided only for personal Entities.'
    #
    # def test_error_on_no_user_in_personal_entity(self):
    #     """Test error on validating data in EntitySerializer when user was not provided for personal Entity."""
    #     payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': Entity.PERSONAL, 'user': None}
    #
    #     serializer = EntitySerializer(data=payload)
    #     with pytest.raises(ValidationError) as exc:
    #         serializer.is_valid(raise_exception=True)
    #     assert str(exc.value.detail['non_field_errors'][0]) == 'User was not provided for personal Entity.'
    #
    # def test_get_entity_details(self, api_client: APIClient, base_user: Any, entity_factory: FactoryMetaClass):
    #     """Test get Entity details."""
    #     api_client.force_authenticate(base_user)
    #     personal_entity = entity_factory(user=base_user, type=Entity.PERSONAL)
    #     global_entity = entity_factory(user=None, type=Entity.GLOBAL)
    #     for entity in [personal_entity, global_entity]:
    #         url = entity_detail_url(entity.id)
    #
    #         response = api_client.get(url)
    #         serializer = EntitySerializer(entity)
    #
    #         assert response.status_code == status.HTTP_200_OK
    #         assert response.data == serializer.data
    #
    # def test_error_get_deposit_details_unauthenticated(self, api_client: APIClient, entity_factory: FactoryMetaClass):
    #     """Test error on getting Entity details being unauthenticated."""
    #     entity = entity_factory()
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.get(url)
    #
    #     assert response.status_code == status.HTTP_401_UNAUTHORIZED
    #
    # def test_error_get_other_user_personal_entity_details(
    #     self, api_client: APIClient, user_factory: FactoryMetaClass, entity_factory: FactoryMetaClass
    # ):
    #     """Test error on getting other user's personal Entity details."""
    #     user_1 = user_factory()
    #     user_2 = user_factory()
    #     entity = entity_factory(user=user_1)
    #     api_client.force_authenticate(user_2)
    #
    #     url = entity_detail_url(entity.id)
    #     response = api_client.get(url)
    #
    #     assert response.status_code == status.HTTP_404_NOT_FOUND
    #
    # @pytest.mark.parametrize('param, value', [('name', 'New name'), ('description', 'New description')])
    # def test_personal_entity_partial_update(
    #     self, api_client: APIClient, base_user: Any, entity_factory: FactoryMetaClass, param: str, value: Any
    # ):
    #     """Test partial update of personal Entity"""
    #     api_client.force_authenticate(base_user)
    #     entity = entity_factory(user=base_user, type=Entity.PERSONAL, name='Entity', description='My entity')
    #     payload = {param: value}
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     entity.refresh_from_db()
    #     assert getattr(entity, param) == payload[param]
    #
    # @pytest.mark.parametrize('param, value', [('name', 'New name'), ('description', 'New description')])
    # def test_global_entity_partial_update(
    #     self, api_client: APIClient, admin_user: Any, entity_factory: FactoryMetaClass, param: str, value: Any
    # ):
    #     """Test partial update of global Entity as admin user."""
    #     api_client.force_authenticate(admin_user)
    #     entity = entity_factory(user=None, type=Entity.GLOBAL, name='Entity', description='My entity')
    #     payload = {param: value}
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.patch(url, payload)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     entity.refresh_from_db()
    #     assert getattr(entity, param) == payload[param]
    #
    # @pytest.mark.parametrize('param, value', [('name', 'Old name')])
    # def test_error_on_entity_partial_update(
    #     self, api_client: APIClient, admin_user: Any, entity_factory: FactoryMetaClass, param: str, value: Any
    # ):
    #     """Test error on partial update of a Deposit."""
    #     api_client.force_authenticate(admin_user)
    #     entity_factory(user=None, name='Old name', description='My old entity')
    #     entity = entity_factory(user=None, name='New name', description='My new entity')
    #     old_value = getattr(entity, param)
    #     payload = {param: value}
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.patch(url, payload)
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     entity.refresh_from_db()
    #     assert getattr(entity, param) == old_value
    #
    # def test_personal_entity_full_update(self, api_client: APIClient, base_user: Any,
    # entity_factory: FactoryMetaClass):
    #     """Test successful full update of personal Entity"""
    #     api_client.force_authenticate(base_user)
    #     payload_old = {'name': 'Name', 'description': 'Selling stuff.', 'type': Entity.PERSONAL}
    #     payload_new = {'name': 'New name', 'description': 'Selling NEW stuff.', 'type': Entity.PERSONAL}
    #     entity = entity_factory(user=base_user, **payload_old)
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.put(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     entity.refresh_from_db()
    #     assert entity.user == base_user
    #     for k, v in payload_new.items():
    #         assert getattr(entity, k) == v
    #
    # def test_global_entity_full_update(self, api_client: APIClient, admin_user: Any,
    # entity_factory: FactoryMetaClass):
    #     """Test successful full update of global Entity"""
    #     api_client.force_authenticate(admin_user)
    #     payload_old = {'name': 'Name', 'description': 'Selling stuff.', 'type': Entity.GLOBAL}
    #     payload_new = {'name': 'New name', 'description': 'Selling NEW stuff.', 'type': Entity.GLOBAL}
    #     entity = entity_factory(user=None, **payload_old)
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.put(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_200_OK
    #     entity.refresh_from_db()
    #     assert entity.user is None
    #     for k, v in payload_new.items():
    #         assert getattr(entity, k) == v
    #
    # @pytest.mark.parametrize(
    #     'payload_new',
    #     [
    #         {'name': 'Old personal seller', 'description': 'Selling stuff.', 'type': Entity.PERSONAL},
    #         {'name': 'New personal seller', 'description': 'Selling stuff.', 'type': Entity.GLOBAL},
    #     ],
    # )
    # def test_error_on_entity_full_update(
    #     self, api_client: APIClient, base_user: Any, entity_factory: FactoryMetaClass, payload_new: dict
    # ):
    #     """Test error on full update of a Entity."""
    #     api_client.force_authenticate(base_user)
    #     entity_factory(
    #         user=base_user, name='Old personal seller', description='Selling old stuff.', type=Entity.PERSONAL
    #     )
    #     entity_factory(user=None, name='Old global seller', description='Selling global stuff.', type=Entity.GLOBAL)
    #     payload_old = {'name': 'New personal seller', 'description': 'Selling stuff.', 'type': Entity.PERSONAL}
    #
    #     entity = entity_factory(user=base_user, **payload_old)
    #     url = entity_detail_url(entity.id)
    #
    #     response = api_client.put(url, payload_new)
    #
    #     assert response.status_code == status.HTTP_400_BAD_REQUEST
    #     entity.refresh_from_db()
    #     for k, v in payload_old.items():
    #         assert getattr(entity, k) == v
    #
    # def test_delete_personal_entity(self, api_client: APIClient, base_user: Any, entity_factory: FactoryMetaClass):
    #     """Test deleting personal Entity."""
    #     api_client.force_authenticate(base_user)
    #     entity = entity_factory(user=base_user)
    #     url = entity_detail_url(entity.id)
    #
    #     assert base_user.personal_entities.all().count() == 1
    #
    #     response = api_client.delete(url)
    #
    #     assert response.status_code == status.HTTP_204_NO_CONTENT
    #     assert not base_user.personal_entities.all().exists()
    #
    # def test_delete_global_entity(self, api_client: APIClient, admin_user: Any, entity_factory: FactoryMetaClass):
    #     """Test deleting global Entity."""
    #     api_client.force_authenticate(admin_user)
    #     entity = entity_factory(user=None)
    #     url = entity_detail_url(entity.id)
    #
    #     assert Entity.global_entities.all().count() == 1
    #
    #     response = api_client.delete(url)
    #
    #     assert response.status_code == status.HTTP_204_NO_CONTENT
    #     assert not Entity.global_entities.all().exists()
    #
    # def test_error_on_delete_global_entity_by_not_admin(
    #     self, api_client: APIClient, base_user: Any, entity_factory: FactoryMetaClass
    # ):
    #     """Test error on attempt to delete global Entity by user, that's not an admin."""
    #     api_client.force_authenticate(base_user)
    #     entity = entity_factory(user=None)
    #     url = entity_detail_url(entity.id)
    #
    #     assert Entity.global_entities.all().count() == 1
    #
    #     response = api_client.delete(url)
    #
    #     assert response.status_code == status.HTTP_403_FORBIDDEN
    #     assert Entity.global_entities.all().count() == 1
