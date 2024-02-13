import pytest
from django.db import DataError
from entities.models import Entity


@pytest.mark.django_db
class TestEntityModel:
    """Tests for Entity model"""

    def test_create_entity_successfully(self, user):
        """Test creating Entity successfully."""
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'user': user, 'is_personal': True}

        entity = Entity.objects.create(**payload)

        for key in payload:
            assert getattr(entity, key) == payload[key]
        assert Entity.objects.filter(user=user).count() == 1
        assert str(entity) == entity.name

    def test_create_two_entities_successfully(self, user):
        """Test creating two Entities successfully."""
        payload_1 = {'name': 'Personal seller', 'description': 'Selling stuff.', 'user': user, 'is_personal': True}
        payload_2 = {'name': 'Global seller', 'description': 'Selling stuff.', 'user': None, 'is_personal': False}

        entity_1 = Entity.objects.create(**payload_1)
        entity_2 = Entity.objects.create(**payload_2)

        for entity, payload in [(entity_1, payload_1), (entity_2, payload_2)]:
            for key in payload:
                assert getattr(entity, key) == payload[key]
        assert Entity.objects.all().count() == 2

    def test_creating_same_entities_by_two_users(self, user_factory):
        """Test creating entities with the same params by two different users."""
        user_1 = user_factory()
        user_2 = user_factory()
        payload = {'name': 'Seller', 'description': 'Selling stuff.', 'is_personal': True}

        Entity.objects.create(user=user_1, **payload)
        Entity.objects.create(user=user_2, **payload)

        assert Entity.objects.all().count() == 2
        assert Entity.objects.filter(user=user_1).count() == 1
        assert Entity.objects.filter(user=user_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self):
        """Test error on creating entity with name too long."""
        max_length = Entity._meta.get_field('name').max_length

        payload = {'name': (max_length + 1) * 'a', 'user': None, 'description': 'Selling stuff.', 'is_personal': True}

        with pytest.raises(DataError) as exc:
            Entity.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Entity.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(self, user):
        """Test error on creating entity with description too long."""
        max_length = Entity._meta.get_field('description').max_length

        payload = {'name': 'Seller', 'user': None, 'description': (max_length + 1) * 'a', 'is_personal': True}

        with pytest.raises(DataError) as exc:
            Entity.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Entity.objects.all().exists()

    def test_description_blank(self, user):
        """Test successfully create entity with description blank."""
        payload = {'name': 'Seller', 'user': None, 'description': '', 'is_personal': True}

        Entity.objects.create(**payload)

        assert Entity.objects.all().count() == 1
        assert Entity.objects.all().first().description == ''
