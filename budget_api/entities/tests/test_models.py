import pytest
from budgets.models import Budget
from django.db import DataError, IntegrityError
from entities.models import Entity
from factory.base import FactoryMetaClass


@pytest.mark.django_db
class TestEntityModel:
    """Tests for Entity model"""

    PAYLOAD = {
        'name': 'Supermarket',
        'description': 'Supermarket in which I buy food.',
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

    def test_creating_same_entity_for_two_budgets(self, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget model instances in database.
        WHEN: Same Entity instance for different Budgets create attempt with valid data.
        THEN: Two Entity model instances existing in database with given data.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = self.PAYLOAD.copy()
        for budget in (budget_1, budget_2):
            payload['budget'] = budget
            Entity.objects.create(**payload)

        assert Entity.objects.all().count() == 2
        assert budget_1.entities.all().count() == 1
        assert budget_2.entities.all().count() == 1

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
