from typing import Any

import pytest
from django.db.models import Q
from django.urls import reverse
from factory.base import FactoryMetaClass
from rest_framework import status
from rest_framework.exceptions import ValidationError
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

        categories = TransferCategory.objects.all()
        serializer = TransferCategorySerializer(categories, many=True)
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

        categories = TransferCategory.objects.filter(
            Q(scope=TransferCategory.GLOBAL) | Q(scope=TransferCategory.PERSONAL, user=user)
        ).distinct()
        serializer = TransferCategorySerializer(categories, many=True)
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
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_201_CREATED
        assert not admin_user.personal_transfer_categories.all().exists()
        assert TransferCategory.global_transfer_categories.all().count() == 1
        category = TransferCategory.objects.get(id=response.data['id'])
        for key in payload:
            assert getattr(category, key) == payload[key]
        serializer = TransferCategorySerializer(category)
        assert response.data == serializer.data
        assert category.user is None

    def test_error_create_global_transfer_category_by_non_admin_user(self, api_client: APIClient, base_user: Any):
        """Test error on creating global TransferCategory by non admin user."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert not base_user.personal_transfer_categories.all().exists()
        assert not TransferCategory.global_transfer_categories.all().exists()

    def test_create_same_personal_transfer_category_by_two_users(self, api_client: APIClient, user_factory: Any):
        """Test creating personal TransferCategory with the same params by two users."""
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }
        user_1 = user_factory()
        api_client.force_authenticate(user_1)
        api_client.post(TRANSFER_CATEGORIES_URL, payload)

        user_2 = user_factory()
        api_client.force_authenticate(user_2)
        api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert TransferCategory.objects.all().count() == 2
        assert not TransferCategory.global_transfer_categories.all().exists()
        assert user_1.personal_transfer_categories.all().count() == 1
        assert user_2.personal_transfer_categories.all().count() == 1

    def test_error_name_too_long(self, api_client: APIClient, base_user: Any):
        """Test error on creating TransferCategory with name too long."""
        api_client.force_authenticate(base_user)
        max_length = TransferCategory._meta.get_field('name').max_length
        payload = {
            'name': 'A' * (max_length + 1),
            'description': 'My salary',
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }
        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
        assert response.data['name'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not base_user.personal_transfer_categories.all().exists()

    def test_error_global_name_already_used(self, api_client: APIClient, admin_user: Any):
        """Test error on creating global TransferCategory with already used name."""
        api_client.force_authenticate(admin_user)
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }
        TransferCategory.objects.create(**payload)

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][0] == 'Global transfer category with given name already exists.'
        assert TransferCategory.global_transfer_categories.all().count() == 1

    def test_error_personal_name_already_used(self, api_client: APIClient, base_user: Any):
        """Test error on creating personal TransferCategory with already used name."""
        api_client.force_authenticate(base_user)
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }
        TransferCategory.objects.create(user=base_user, **payload)

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data
        assert response.data['non_field_errors'][0] == 'Personal transfer category with given name already exists.'
        assert base_user.personal_transfer_categories.all().count() == 1

    def test_error_description_too_long(self, api_client: APIClient, base_user: Any):
        """Test error on creating TransferCategory with description too long."""
        api_client.force_authenticate(base_user)
        max_length = TransferCategory._meta.get_field('description').max_length
        payload = {
            'name': 'Salary',
            'description': 'A' * (max_length + 1),
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        response = api_client.post(TRANSFER_CATEGORIES_URL, payload)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'description' in response.data
        assert response.data['description'][0] == f'Ensure this field has no more than {max_length} characters.'
        assert not TransferCategory.global_transfer_categories.all().exists()

    def test_error_on_user_in_global_transfer_category(self, base_user: Any):
        """Test error on validating data in TransferCategorySerializer when user was provided for global
        TransferCategory."""
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
            'user': base_user.pk,
        }
        serializer = TransferCategorySerializer(data=payload)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert (
            str(exc.value.detail['non_field_errors'][0]) == 'User can be provided only for personal transfer category.'
        )

    def test_error_on_no_user_in_personal_transfer_category(self):
        """Test error on validating data in TransferCategorySerializer when user was not provided for personal
        TransferCategory."""
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }
        serializer = TransferCategorySerializer(data=payload)
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert str(exc.value.detail['non_field_errors'][0]) == 'User was not provided for personal transfer category.'

    def test_get_transfer_category_details(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test get TransferCategory details."""
        api_client.force_authenticate(base_user)
        personal_category = transfer_category_factory(user=base_user, scope=TransferCategory.PERSONAL)
        global_category = transfer_category_factory(user=None, scope=TransferCategory.GLOBAL)
        for category in [personal_category, global_category]:
            url = transfer_category_detail_url(category.id)

            response = api_client.get(url)
            serializer = TransferCategorySerializer(category)

            assert response.status_code == status.HTTP_200_OK
            assert response.data == serializer.data

    def test_error_get_transfer_category_details_unauthenticated(
        self, api_client: APIClient, transfer_category_factory: FactoryMetaClass
    ):
        """Test error on getting TransferCategory details being unauthenticated."""
        category = transfer_category_factory()
        url = transfer_category_detail_url(category.id)

        response = api_client.get(url)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_error_get_other_user_personal_transfer_category_details(
        self, api_client: APIClient, user_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """Test error on getting other user's personal TransferCategory details."""
        user_1 = user_factory()
        user_2 = user_factory()
        category = transfer_category_factory(user=user_1)
        api_client.force_authenticate(user_2)

        url = transfer_category_detail_url(category.id)
        response = api_client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        'param, value',
        [
            ('name', 'New name'),
            ('description', 'New description'),
            ('category_type', TransferCategory.EXPENSE),
            ('is_active', False),
        ],
    )
    def test_personal_transfer_category_partial_update(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass, param: str, value: Any
    ):
        """Test partial update of personal TransferCategory."""
        api_client.force_authenticate(base_user)
        category = transfer_category_factory(
            user=base_user,
            category_type=TransferCategory.INCOME,
            scope=TransferCategory.PERSONAL,
            name='Name',
            description='Description',
            is_active=True,
        )
        payload = {param: value}
        url = transfer_category_detail_url(category.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, param) == payload[param]

    @pytest.mark.parametrize(
        'param, value',
        [
            ('name', 'New name'),
            ('description', 'New description'),
            ('category_type', TransferCategory.EXPENSE),
            ('is_active', False),
        ],
    )
    def test_global_transfer_category_partial_update(
        self,
        api_client: APIClient,
        admin_user: Any,
        transfer_category_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """Test partial update of global TransferCategory as admin user."""
        api_client.force_authenticate(admin_user)
        category = transfer_category_factory(
            user=None,
            category_type=TransferCategory.INCOME,
            scope=TransferCategory.GLOBAL,
            name='Name',
            description='Description',
            is_active=True,
        )
        payload = {param: value}
        url = transfer_category_detail_url(category.id)

        response = api_client.patch(url, payload)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert getattr(category, param) == payload[param]

    @pytest.mark.parametrize(
        'param, value',
        [
            ('name', 'Old name'),
        ],
    )
    def test_error_on_transfer_category_partial_update(
        self,
        api_client: APIClient,
        admin_user: Any,
        transfer_category_factory: FactoryMetaClass,
        param: str,
        value: Any,
    ):
        """Test error on partial update of a Deposit."""
        api_client.force_authenticate(admin_user)
        transfer_category_factory(
            user=None,
            category_type=TransferCategory.EXPENSE,
            scope=TransferCategory.GLOBAL,
            name='Old name',
            description='Old description',
            is_active=False,
        )
        category = transfer_category_factory(
            user=None,
            category_type=TransferCategory.INCOME,
            scope=TransferCategory.GLOBAL,
            name='New name',
            description='New description',
            is_active=True,
        )
        old_value = getattr(category, param)
        payload = {param: value}
        url = transfer_category_detail_url(category.id)

        response = api_client.patch(url, payload)
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category.refresh_from_db()
        assert getattr(category, param) == old_value

    def test_personal_transfer_category_full_update(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test successful full update of personal TransferCategory"""
        api_client.force_authenticate(base_user)
        payload_old = {
            'category_type': TransferCategory.EXPENSE,
            'scope': TransferCategory.PERSONAL,
            'name': 'Name',
            'description': 'Description',
        }
        payload_new = {
            'category_type': TransferCategory.INCOME,
            'scope': TransferCategory.PERSONAL,
            'name': 'New name',
            'description': 'New description',
        }
        category = transfer_category_factory(user=base_user, **payload_old)
        url = transfer_category_detail_url(category.id)

        response = api_client.put(url, payload_new)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.user == base_user
        for k, v in payload_new.items():
            assert getattr(category, k) == v

    def test_global_transfer_category_full_update(
        self, api_client: APIClient, admin_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test successful full update of global TransferCategory"""
        api_client.force_authenticate(admin_user)
        payload_old = {
            'category_type': TransferCategory.EXPENSE,
            'scope': TransferCategory.GLOBAL,
            'name': 'Name',
            'description': 'Description',
        }
        payload_new = {
            'category_type': TransferCategory.INCOME,
            'scope': TransferCategory.GLOBAL,
            'name': 'New name',
            'description': 'New description',
        }
        category = transfer_category_factory(user=None, **payload_old)
        url = transfer_category_detail_url(category.id)

        response = api_client.put(url, payload_new)

        assert response.status_code == status.HTTP_200_OK
        category.refresh_from_db()
        assert category.user is None
        for k, v in payload_new.items():
            assert getattr(category, k) == v

    @pytest.mark.parametrize(
        'payload_new',
        [
            {'name': 'Old personal name', 'scope': TransferCategory.PERSONAL},
            {'name': 'New personal seller', 'scope': TransferCategory.GLOBAL},
        ],
    )
    def test_error_on_transfer_category_full_update(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass, payload_new: dict
    ):
        """Test error on full update of TransferCategory."""
        api_client.force_authenticate(base_user)
        transfer_category_factory(
            user=None,
            category_type=TransferCategory.EXPENSE,
            scope=TransferCategory.GLOBAL,
            name='Old personal name',
            description='Old personal description',
        )
        transfer_category_factory(
            user=None,
            category_type=TransferCategory.INCOME,
            scope=TransferCategory.GLOBAL,
            name='Old global name',
            description='Old global description',
        )

        payload_old = {
            'category_type': TransferCategory.EXPENSE,
            'scope': TransferCategory.PERSONAL,
            'name': 'New personal name',
            'description': 'New personal description',
        }

        category = transfer_category_factory(user=base_user, **payload_old)
        url = transfer_category_detail_url(category.id)

        response = api_client.put(url, payload_new)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        category.refresh_from_db()
        for k, v in payload_old.items():
            assert getattr(category, k) == v

    def test_delete_personal_transfer_category(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test deleting personal TransferCategory."""
        api_client.force_authenticate(base_user)
        category = transfer_category_factory(user=base_user)
        url = transfer_category_detail_url(category.id)

        assert base_user.personal_transfer_categories.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not base_user.personal_transfer_categories.all().exists()

    def test_delete_global_transfer_categories(
        self, api_client: APIClient, admin_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test deleting global TransferCategory."""
        api_client.force_authenticate(admin_user)
        category = transfer_category_factory(user=None)
        url = transfer_category_detail_url(category.id)

        assert TransferCategory.global_transfer_categories.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not TransferCategory.global_transfer_categories.all().exists()

    def test_error_on_delete_global_transfer_category_by_not_admin(
        self, api_client: APIClient, base_user: Any, transfer_category_factory: FactoryMetaClass
    ):
        """Test error on attempt to delete global TransferCategory by user, that's not an admin."""
        api_client.force_authenticate(base_user)
        category = transfer_category_factory(user=None)
        url = transfer_category_detail_url(category.id)

        assert TransferCategory.global_transfer_categories.all().count() == 1

        response = api_client.delete(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert TransferCategory.global_transfer_categories.all().count() == 1
