import pytest
from budgets.models import Budget
from django.db import DataError
from factory.base import FactoryMetaClass
from transfers.models import TransferCategory


@pytest.mark.django_db
class TestTransferCategoryModel:
    """Tests for TransferCategory model"""

    PAYLOAD = {
        'name': 'Food',
        'description': 'Category for food expenses.',
        'is_active': True,
        'expense_group': TransferCategory.ExpenseGroups.MOST_IMPORTANT,
        'income_group': None,
    }

    def test_create_category_without_owner(self, budget: Budget):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory without owner provided.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        category = TransferCategory.objects.create(budget=budget, **self.PAYLOAD)

        for key in self.PAYLOAD:
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner is None
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f'{category.name} ({category.budget.name})'

    def test_create_category_with_owner(self, user_factory: FactoryMetaClass, budget: Budget):
        """
        GIVEN: Budget model instance in database. Valid payload for TransferCategory with owner provided.
        WHEN: TransferCategory instance create attempt with valid data.
        THEN: TransferCategory model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        category_owner = user_factory()
        budget.members.add(category_owner)
        payload['owner'] = category_owner

        category = TransferCategory.objects.create(budget=budget, **payload)

        for key in payload:
            if key == 'owner':
                continue
            assert getattr(category, key) == self.PAYLOAD[key]
        assert category.owner == category_owner
        assert TransferCategory.objects.filter(budget=budget).count() == 1
        assert str(category) == f'{category.name} ({category.budget.name})'

    def test_creating_same_category_for_two_budgets(self, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget model instances in database.
        WHEN: Same TransferCategory instance for different Budgets create attempt with valid data.
        THEN: Two TransferCategory model instances existing in database with given data.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = self.PAYLOAD.copy()
        for budget in (budget_1, budget_2):
            payload['budget'] = budget
            TransferCategory.objects.create(**payload)

        assert TransferCategory.objects.all().count() == 2
        assert TransferCategory.objects.filter(budget=budget_1).count() == 1
        assert TransferCategory.objects.filter(budget=budget_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('field_name', ['name', 'description'])
    def test_error_value_too_long(self, budget: Budget, field_name: str):
        """
        GIVEN: Budget model instance in database.
        WHEN: TransferCategory instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = TransferCategory._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * 'a'

        with pytest.raises(DataError) as exc:
            TransferCategory.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not TransferCategory.objects.filter(budget=budget).exists()
