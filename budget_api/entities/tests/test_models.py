import pytest
from django.core.exceptions import ValidationError
from django.db import DataError
from entities.models import Entity


@pytest.mark.django_db
class TestEntityModel:
    """Tests for Entity model"""

    def test_create_personal_entity_successfully(self, user):
        """Test creating personal Entity successfully."""
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'user': user, 'type': 'PERSONAL'}

        entity = Entity.objects.create(**payload)

        for key in payload:
            assert getattr(entity, key) == payload[key]
        assert user.personal_entities.count() == 1
        assert Entity.objects.all().count() == 1
        assert not Entity.global_entities.all().exists()
        assert str(entity) == entity.name

    def test_create_global_entity_successfully(self):
        """Test creating global Entity successfully."""
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'user': None, 'type': 'GLOBAL'}

        entity = Entity.objects.create(**payload)

        for key in payload:
            assert getattr(entity, key) == payload[key]
        assert Entity.objects.all().count() == 1
        assert Entity.global_entities.all().count() == 1
        assert str(entity) == entity.name

    def test_creating_same_entities_by_two_users(self, user_factory):
        """Test creating personal entities with the same params by two different users."""
        user_1 = user_factory()
        user_2 = user_factory()
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'type': 'PERSONAL'}

        Entity.objects.create(user=user_1, **payload)
        Entity.objects.create(user=user_2, **payload)

        assert Entity.objects.all().count() == 2
        assert user_1.personal_entities.count() == 1
        assert user_2.personal_entities.count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self):
        """Test error on creating entity with name too long."""
        max_length = Entity._meta.get_field('name').max_length

        payload = {'name': (max_length + 1) * 'a', 'user': None, 'description': 'Selling stuff.', 'type': 'GLOBAL'}

        with pytest.raises(DataError) as exc:
            Entity.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Entity.objects.all().exists()

    def test_error_name_already_user_in_personal_entity(self, user):
        """Test error on creating personal Entity, that user has already created."""
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'user': user, 'type': 'PERSONAL'}

        Entity.objects.create(**payload)

        with pytest.raises(ValidationError) as exc:
            Entity.objects.create(**payload)
        assert exc.value.code == 'personal-name-invalid'
        assert exc.value.message == 'name: Personal entity with given name already exists.'

    def test_error_name_already_user_in_global_entity(self):
        """Test error on creating global Entity that was already created."""
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'user': None, 'type': 'GLOBAL'}

        Entity.objects.create(**payload)

        with pytest.raises(ValidationError) as exc:
            Entity.objects.create(**payload)
        assert exc.value.code == 'global-name-invalid'
        assert exc.value.message == 'name: Global entity with given name already exists.'
        assert Entity.objects.all().count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(self, user):
        """Test error on creating entity with description too long."""
        max_length = Entity._meta.get_field('description').max_length

        payload = {'name': 'Seller', 'user': None, 'description': (max_length + 1) * 'a', 'type': 'GLOBAL'}

        with pytest.raises(DataError) as exc:
            Entity.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Entity.objects.all().exists()

    def test_description_blank(self, user):
        """Test successfully create entity with description blank."""
        payload = {'name': 'Seller', 'user': None, 'description': '', 'type': 'GLOBAL'}

        Entity.objects.create(**payload)

        assert Entity.objects.all().count() == 1
        assert Entity.objects.all().first().description == ''

    def test_error_no_user_for_personal_entity(self):
        """Test error on creating personal Entity with no user provided."""
        payload = {'name': 'Seller', 'user': None, 'description': '', 'type': 'PERSONAL'}

        with pytest.raises(ValidationError) as exc:
            Entity.objects.create(**payload)

        assert exc.value.code == 'no-user-for-personal'
        assert exc.value.message == 'user: User was not provided for personal Entity.'
        assert not Entity.objects.all().exists()

    def test_error_user_given_for_global_entity(self, user):
        """Test error on creating global Entity with user provided."""
        payload = {'name': 'Seller', 'user': user, 'description': '', 'type': 'GLOBAL'}

        with pytest.raises(ValidationError) as exc:
            Entity.objects.create(**payload)

        assert exc.value.code == 'user-when-global'
        assert exc.value.message == 'user: User can be provided only for personal Entities.'
        assert not Entity.objects.all().exists()

    def test_deleting_entities_on_user_deletion(self, user):
        """Test removing user personal entities on user deletion."""
        payload_global = {'name': 'Global seller', 'user': None, 'description': '', 'type': 'GLOBAL'}
        Entity.objects.create(**payload_global)
        payload_personal = {'name': 'Personal seller', 'user': user, 'description': '', 'type': 'PERSONAL'}
        Entity.objects.create(**payload_personal)

        assert user.personal_entities.all().count() == 1
        assert Entity.objects.all().count() == 2
        assert Entity.global_entities.all().count() == 1

        user.delete()

        assert Entity.objects.all().count() == 1
        assert Entity.global_entities.all().count() == 1
