import pytest
from budgets.models import Budget
from django.db import DataError, IntegrityError
from entities.models import Entity
from factory.base import FactoryMetaClass


@pytest.mark.django_db
class TestEntityModel:
    """Tests for Entity model"""

    PAYLOAD: dict = {
        'name': 'Supermarket',
        'description': 'Supermarket in which I buy food.',
        'is_active': True,
        'is_deposit': False,
    }

    def test_create_entity_successfully(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Entity instance create attempt with valid data.
        THEN: Entity model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload['budget'] = budget

        entity = Entity.objects.create(**payload)

        for key in payload:
            assert getattr(entity, key) == payload[key]
        assert Entity.objects.filter(budget=budget).count() == 1
        assert str(entity) == f'{entity.name} ({entity.budget.name})'

    def test_create_deposit(self, budget: Budget, entity_factory: FactoryMetaClass, deposit_factory: FactoryMetaClass):
        """
        GIVEN: Budget and two Entities (with is_deposit=False and is_deposit=True) models instances in database.
        WHEN: Calling .deposits Entity manager for objects.
        THEN: Manager returns only object with is_deposit=True.
        """
        entity_factory(budget=budget)
        deposit = deposit_factory(budget=budget)

        entity_qs = Entity.objects.all()
        deposit_qs = Entity.deposits.all()

        assert entity_qs.count() == 2
        assert deposit_qs.count() == 1
        assert deposit in deposit_qs

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('field_name', ['name', 'description'])
    def test_error_value_too_long(self, budget: Budget, field_name: str):
        """
        GIVEN: Budget model instances in database.
        WHEN: Entity instance for different Budgets create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = Entity._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * 'a'

        with pytest.raises(DataError) as exc:
            Entity.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Entity.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, budget: Budget):
        """
        GIVEN: Budget model instances in database.
        WHEN: Entity instance for different Budgets create attempt with name already used in particular Budget.
        THEN: DataError raised.
        """
        payload = self.PAYLOAD.copy()
        payload['budget'] = budget

        Entity.objects.create(**payload)

        with pytest.raises(IntegrityError) as exc:
            Entity.objects.create(**payload)
        assert f'DETAIL:  Key (name, budget_id)=({payload["name"]}, {budget.id}) already exists.' in str(exc.value)
        assert Entity.objects.filter(budget=budget).count() == 1
