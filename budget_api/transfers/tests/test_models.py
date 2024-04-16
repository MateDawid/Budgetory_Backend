import pytest
from django.core.exceptions import ValidationError
from django.db import DataError
from transfers.models.transfer_category import TransferCategory


@pytest.mark.django_db
class TestTransferCategoryModel:
    """Tests for TransferCategory model"""

    def test_create_personal_transfer_category_successfully(self, user):
        """Test creating personal TransferCategory successfully."""
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'user': user,
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        category = TransferCategory.objects.create(**payload)

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert user.personal_transfer_categories.count() == 1
        assert TransferCategory.objects.all().count() == 1
        assert not TransferCategory.global_transfer_categories.all().exists()
        assert str(category) == category.name

    def test_create_global_transfer_category_successfully(self):
        """Test creating global TransferCategory successfully."""
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        category = TransferCategory.objects.create(**payload)

        for key in payload:
            assert getattr(category, key) == payload[key]
        assert TransferCategory.objects.all().count() == 1
        assert TransferCategory.global_transfer_categories.all().count() == 1
        assert str(category) == category.name

    def test_creating_same_transfer_categories_by_two_users(self, user_factory):
        """Test creating personal transfer categories with the same params by two different users."""
        user_1 = user_factory()
        user_2 = user_factory()
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        TransferCategory.objects.create(user=user_1, **payload)
        TransferCategory.objects.create(user=user_2, **payload)

        assert TransferCategory.objects.all().count() == 2
        assert user_1.personal_transfer_categories.count() == 1
        assert user_2.personal_transfer_categories.count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self):
        """Test error on creating transfer category with name too long."""
        max_length = TransferCategory._meta.get_field('name').max_length

        payload = {
            'name': (max_length + 1) * 'a',
            'description': 'Taxes payments.',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        with pytest.raises(DataError) as exc:
            TransferCategory.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not TransferCategory.objects.all().exists()

    def test_error_name_already_user_in_personal_transfer_category(self, user):
        """Test error on creating personal TransferCategory, that user has already created."""
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'user': user,
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        TransferCategory.objects.create(**payload)

        with pytest.raises(ValidationError) as exc:
            TransferCategory.objects.create(**payload)
        assert exc.value.code == 'personal-name-invalid'
        assert exc.value.message == 'name: Personal transfer category with given name already exists.'

    def test_error_name_already_user_in_global_transfer_category(self):
        """Test error on creating global TransferCategory that was already created."""
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        TransferCategory.objects.create(**payload)

        with pytest.raises(ValidationError) as exc:
            TransferCategory.objects.create(**payload)
        assert exc.value.code == 'global-name-invalid'
        assert exc.value.message == 'name: Global transfer category with given name already exists.'
        assert TransferCategory.objects.all().count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(self, user):
        """Test error on creating TransferCategory with description too long."""
        max_length = TransferCategory._meta.get_field('description').max_length

        payload = {
            'name': 'Taxes',
            'description': (max_length + 1) * 'a',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        with pytest.raises(DataError) as exc:
            TransferCategory.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not TransferCategory.objects.all().exists()

    def test_description_blank(self, user):
        """Test successfully create TransferCategory with description blank."""
        payload = {
            'name': 'Taxes',
            'description': '',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        TransferCategory.objects.create(**payload)

        assert TransferCategory.objects.all().count() == 1
        assert TransferCategory.objects.all().first().description == ''

    def test_error_no_user_for_personal_transfer_category(self):
        """Test error on creating personal TransferCategory with no user provided."""
        payload = {
            'name': 'Salary',
            'description': 'My salary',
            'user': None,
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }

        with pytest.raises(ValidationError) as exc:
            TransferCategory.objects.create(**payload)

        assert exc.value.code == 'no-user-for-personal'
        assert exc.value.message == 'user: User was not provided for personal transfer category.'
        assert not TransferCategory.objects.all().exists()

    def test_error_user_given_for_global_transfer_category(self, user):
        """Test error on creating global TransferCategory with user provided."""
        payload = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'user': user,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }

        with pytest.raises(ValidationError) as exc:
            TransferCategory.objects.create(**payload)

        assert exc.value.code == 'user-when-global'
        assert exc.value.message == 'user: User can be provided only for personal transfer category.'
        assert not TransferCategory.objects.all().exists()

    def test_deleting_transfer_categories_on_user_deletion(self, user):
        """Test removing user personal TransferCategory on user deletion."""
        payload_global = {
            'name': 'Taxes',
            'description': 'Taxes payments.',
            'user': None,
            'scope': TransferCategory.GLOBAL,
            'category_type': TransferCategory.EXPENSE,
            'is_active': True,
        }
        TransferCategory.objects.create(**payload_global)
        payload_personal = {
            'name': 'Salary',
            'description': 'My salary',
            'user': user,
            'scope': TransferCategory.PERSONAL,
            'category_type': TransferCategory.INCOME,
            'is_active': True,
        }
        TransferCategory.objects.create(**payload_personal)

        assert user.personal_transfer_categories.all().count() == 1
        assert TransferCategory.objects.all().count() == 2
        assert TransferCategory.global_transfer_categories.all().count() == 1

        user.delete()

        assert TransferCategory.objects.all().count() == 1
        assert TransferCategory.global_transfer_categories.all().count() == 1
