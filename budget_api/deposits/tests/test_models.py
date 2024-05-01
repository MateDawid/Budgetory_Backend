import pytest
from budgets.models import Budget
from deposits.models import Deposit
from django.db import DataError, IntegrityError
from factory.base import FactoryMetaClass


@pytest.mark.django_db
class TestDepositModel:
    """Tests for Deposit model"""

    def test_create_deposit_successfully(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Deposit instance create attempt with valid data.
        THEN: Deposit model instance exists in database with given data.
        """
        payload = {
            'budget': budget,
            'name': 'Bank account',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': 'User\'s bank account',
            'is_active': True,
            'owner': budget.owner,
        }

        deposit = Deposit.objects.create(**payload)

        for key in payload:
            assert getattr(deposit, key) == payload[key]
        assert Deposit.objects.filter(budget=budget).count() == 1
        assert str(deposit) == f'{deposit.name} ({deposit.budget.name})'

    def test_create_deposit_without_owner(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Deposit instance create attempt with valid data with 'owner' = None.
        THEN: Deposit model instance exists in database with given data.
        """
        payload = {
            'budget': budget,
            'name': 'Bank account',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': 'User\'s bank account',
            'is_active': True,
            'owner': None,
        }

        deposit = Deposit.objects.create(**payload)

        assert Deposit.objects.filter(budget=budget).count() == 1
        assert deposit.owner is None

    def test_creating_same_deposit_for_two_budgets(self, budget_factory: FactoryMetaClass):
        """
        GIVEN: Two Budget model instances in database.
        WHEN: Same Deposit instance for different Budgets create attempt with valid data.
        THEN: Two Deposit model instances existing in database with given data.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = {
            'name': 'Bank account',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': 'User\'s bank account',
            'is_active': True,
        }
        for budget in (budget_1, budget_2):
            payload['budget'] = budget
            payload['owner'] = budget.owner
            Deposit.objects.create(**payload)

        assert Deposit.objects.all().count() == 2
        assert Deposit.objects.filter(budget=budget_1).count() == 1
        assert Deposit.objects.filter(budget=budget_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, budget: Budget):
        """
        GIVEN: Budget model instances in database.
        WHEN: Deposit instance for different Budgets create attempt with name too long.
        THEN: DataError raised.
        """
        max_length = Deposit._meta.get_field('name').max_length
        payload = {
            'budget': budget,
            'name': (max_length + 1) * 'a',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': 'User\'s bank account',
            'is_active': True,
            'owner': budget.owner,
        }

        with pytest.raises(DataError) as exc:
            Deposit.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Deposit.objects.filter(budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, budget: Budget):
        """
        GIVEN: Budget model instances in database.
        WHEN: Deposit instance for different Budgets create attempt with name already used in particular Budget.
        THEN: DataError raised.
        """
        payload = {
            'budget': budget,
            'name': 'Bank account',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': 'User\'s bank account',
            'is_active': True,
            'owner': budget.owner,
        }
        Deposit.objects.create(**payload)

        with pytest.raises(IntegrityError) as exc:
            Deposit.objects.create(**payload)
        assert f'DETAIL:  Key (name, budget_id)=({payload["name"]}, {budget.id}) already exists.' in str(exc.value)
        assert Deposit.objects.filter(budget=budget).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(self, budget: Budget):
        """
        GIVEN: Budget model instances in database.
        WHEN: Deposit instance for different Budgets create attempt with description too long.
        THEN: DataError raised.
        """
        max_length = Deposit._meta.get_field('description').max_length

        payload = {
            'budget': budget,
            'name': 'Deposit',
            'deposit_type': Deposit.DepositTypes.PERSONAL,
            'description': (max_length + 1) * 'a',
            'is_active': True,
            'owner': budget.owner,
        }

        with pytest.raises(DataError) as exc:
            Deposit.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Deposit.objects.filter(budget=budget).exists()
