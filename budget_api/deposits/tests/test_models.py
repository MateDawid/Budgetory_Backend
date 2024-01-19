import pytest
from deposits.models import Deposit
from django.db import DataError, IntegrityError


@pytest.mark.django_db
class TestDepositModel:
    """Tests for Deposit model"""

    def test_create_deposit_successfully(self, user):
        """Test creating Deposit successfully."""
        payload = {'name': 'Bank account', 'user': user, 'description': 'User\'s bank account', 'is_active': True}

        deposit = Deposit.objects.create(**payload)

        for key in payload:
            assert getattr(deposit, key) == payload[key]
        assert Deposit.objects.filter(user=user).count() == 1
        assert str(deposit) == f'{deposit.name} ({deposit.user.email})'

    def test_create_two_deposits_successfully(self, user):
        """Test creating two consecutive BudgetingPeriod successfully."""
        payload_1 = {'name': 'Bank account', 'user': user, 'description': 'User\'s bank account', 'is_active': True}
        payload_2 = {'name': 'Cash', 'user': user, 'description': 'User\'s cash', 'is_active': True}

        deposit_1 = Deposit.objects.create(**payload_1)
        deposit_2 = Deposit.objects.create(**payload_2)

        for deposit, payload in [(deposit_1, payload_1), (deposit_2, payload_2)]:
            for key in payload:
                assert getattr(deposit, key) == payload[key]
        assert Deposit.objects.filter(user=user).count() == 2

    def test_creating_same_deposit_by_two_users(self, user_factory):
        """Test creating period with the same params by two different users."""
        user_1 = user_factory()
        user_2 = user_factory()
        payload = {'name': 'Bank account', 'description': 'User\'s bank account', 'is_active': True}

        Deposit.objects.create(user=user_1, **payload)
        Deposit.objects.create(user=user_2, **payload)

        assert Deposit.objects.all().count() == 2
        assert Deposit.objects.filter(user=user_1).count() == 1
        assert Deposit.objects.filter(user=user_2).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, user):
        """Test error on creating deposit with name too long."""
        max_length = Deposit._meta.get_field('name').max_length

        payload = {'name': (max_length + 1) * 'a', 'user': user, 'description': 'User\'s deposit', 'is_active': True}

        with pytest.raises(DataError) as exc:
            Deposit.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Deposit.objects.filter(user=user).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, user):
        """Test error on creating deposit with already used name by the same user."""
        payload = {'name': 'Bank account', 'user': user, 'description': 'User\'s bank account', 'is_active': True}
        Deposit.objects.create(**payload)

        with pytest.raises(IntegrityError) as exc:
            Deposit.objects.create(**payload)
        assert f'DETAIL:  Key (name, user_id)=({payload["name"]}, {user.id}) already exists.' in str(exc.value)
        assert Deposit.objects.filter(user=user).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(self, user):
        """Test error on creating deposit with description too long."""
        max_length = Deposit._meta.get_field('description').max_length

        payload = {'name': 'Deposit', 'user': user, 'description': (max_length + 1) * 'a', 'is_active': True}

        with pytest.raises(DataError) as exc:
            Deposit.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not Deposit.objects.filter(user=user).exists()

    def test_description_blank(self, user):
        """Test successfully create deposit with description blank."""
        payload = {'name': 'Bank account', 'user': user, 'description': '', 'is_active': True}

        Deposit.objects.create(**payload)

        assert Deposit.objects.all().count() == 1
        assert Deposit.objects.get(user=user).description == ''
