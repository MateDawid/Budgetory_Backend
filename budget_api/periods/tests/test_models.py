import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from periods.models import BudgetingPeriod


@pytest.mark.django_db
class TestBudgetingPeriodModel:
    """Tests for BudgetingPeriod model"""

    payload: dict = {
        'name': '2023_01',
        'date_start': datetime.date(day=1, month=1, year=2023),
        'date_end': datetime.date(day=31, month=1, year=2023),
    }

    def test_create_first_period_successful(self, user):
        """Test creating first user BudgetingPeriod successfully."""
        payload = self.payload.copy()
        payload['user'] = user

        budgeting_period = BudgetingPeriod.objects.create(**payload)
        assert budgeting_period.name == payload['name']
        assert budgeting_period.user == payload['user']
        assert budgeting_period.date_start == payload['date_start']
        assert budgeting_period.date_end == payload['date_end']
        assert budgeting_period.is_active is False
        assert BudgetingPeriod.objects.filter(user=user).count() == 1
        assert str(budgeting_period) == f'{budgeting_period.name} ({budgeting_period.user.email})'

    def test_create_two_periods_successful(self, user):
        """Test creating two consecutive BudgetingPeriod successfully."""
        payload_1 = self.payload.copy()
        payload_1['user'] = user
        payload_2 = {
            'name': '2023_02',
            'user': user,
            'date_start': datetime.date(day=1, month=2, year=2023),
            'date_end': datetime.date(day=28, month=2, year=2023),
        }
        budgeting_period_1 = BudgetingPeriod.objects.create(**payload_1)
        budgeting_period_2 = BudgetingPeriod.objects.create(**payload_2)
        for budgeting_period, payload in [(budgeting_period_1, payload_1), (budgeting_period_2, payload_2)]:
            assert budgeting_period.name == payload['name']
            assert budgeting_period.user == payload['user']
            assert budgeting_period.date_start == payload['date_start']
            assert budgeting_period.date_end == payload['date_end']
            assert budgeting_period.is_active is False
        assert BudgetingPeriod.objects.filter(user=user).count() == 2

    def test_creating_same_period_by_two_users(self, user_factory):
        """Test creating period with the same params by two different users."""
        payload_1 = self.payload.copy()
        payload_1['user'] = user_factory()
        payload_1['is_active'] = True

        payload_2 = self.payload.copy()
        payload_2['user'] = user_factory()
        payload_1['is_active'] = True

        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)

        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=payload_1['user']).count() == 1
        assert BudgetingPeriod.objects.filter(user=payload_2['user']).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, user):
        """Test error on creating period with name too long."""
        payload = self.payload.copy()
        payload['user'] = user
        payload['name'] = 129 * 'a'

        with pytest.raises(DataError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert str(exc.value) == 'value too long for type character varying(128)\n'
        assert not BudgetingPeriod.objects.filter(user=user).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, user):
        """Test error on creating period with already used name by the same user."""
        payload = self.payload.copy()
        payload['user'] = user
        BudgetingPeriod.objects.create(**payload)

        payload['date_start'] = datetime.date(day=1, month=2, year=2023)
        payload['date_end'] = datetime.date(day=28, month=2, year=2023)
        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert f'DETAIL:  Key (name, user_id)=({payload["name"]}, {user.id}) already exists.' in str(exc.value)
        assert BudgetingPeriod.objects.filter(user=user).count() == 1

    def test_error_is_active_set_already(self, user):
        """Test error on making period active, when another user period active already."""
        payload_1 = self.payload.copy()
        payload_1['user'] = user
        payload_1['is_active'] = True
        active_period = BudgetingPeriod.objects.create(**payload_1)

        payload_2 = {
            'name': '2023_02',
            'user': user,
            'date_start': datetime.date(day=1, month=2, year=2023),
            'date_end': datetime.date(day=28, month=2, year=2023),
            'is_active': True,
        }
        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload_2)
        assert str(exc.value) == "['is_active: User already has active budgeting period.']"
        assert BudgetingPeriod.objects.filter(user=user).count() == 1
        assert BudgetingPeriod.objects.filter(user=user).first() == active_period

    @pytest.mark.django_db(transaction=True)
    def test_error_is_active_none(self, user):
        """Test error on creating period with is_active set to None."""
        payload = self.payload.copy()
        payload['user'] = user
        payload['is_active'] = None
        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert 'null value in column "is_active"' in str(exc.value)
        assert not BudgetingPeriod.objects.filter(user=user).exists()
