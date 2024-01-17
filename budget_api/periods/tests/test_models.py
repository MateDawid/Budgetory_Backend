from datetime import date
from typing import Union

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from periods.models import BudgetingPeriod


@pytest.mark.django_db
class TestBudgetingPeriodModel:
    """Tests for BudgetingPeriod model"""

    def test_create_first_period_successful(self, user):
        """Test creating first user BudgetingPeriod successfully."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }

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
        payload_1 = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        payload_2 = {
            'name': '2023_02',
            'user': user,
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
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
        payload_1 = {
            'name': '2023_01',
            'user': user_factory(),
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        payload_2 = {
            'name': '2023_01',
            'user': user_factory(),
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }

        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)

        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=payload_1['user']).count() == 1
        assert BudgetingPeriod.objects.filter(user=payload_2['user']).count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_name_too_long(self, user):
        """Test error on creating period with name too long."""
        max_length = BudgetingPeriod._meta.get_field('name').max_length
        payload = {
            'name': (max_length + 1) * 'a',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }

        with pytest.raises(DataError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert str(exc.value) == f'value too long for type character varying({max_length})\n'
        assert not BudgetingPeriod.objects.filter(user=user).exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_name_already_used(self, user):
        """Test error on creating period with already used name by the same user."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        BudgetingPeriod.objects.create(**payload)

        payload['date_start'] = date(2023, 2, 1)
        payload['date_end'] = date(2023, 2, 28)
        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert f'DETAIL:  Key (name, user_id)=({payload["name"]}, {user.id}) already exists.' in str(exc.value)
        assert BudgetingPeriod.objects.filter(user=user).count() == 1

    def test_create_active_period_successfully(self, user):
        """Test creating period with is_active=True successfully."""
        payload_inactive = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': False,
        }
        payload_active = {
            'name': '2023_02',
            'user': user,
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
            'is_active': True,
        }

        period_inactive = BudgetingPeriod.objects.create(**payload_inactive)
        period_active = BudgetingPeriod.objects.create(**payload_active)
        assert period_inactive.is_active is False
        assert period_active.is_active is True
        assert BudgetingPeriod.objects.filter(user=user).count() == 2

    def test_error_is_active_set_already(self, user):
        """Test error on making period active, when another user period active already."""
        payload_1 = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        active_period = BudgetingPeriod.objects.create(**payload_1)

        payload_2 = {
            'name': '2023_02',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload_2)
        assert exc.value.code == 'active-invalid'
        assert exc.value.message == 'is_active: User already has active budgeting period.'
        assert BudgetingPeriod.objects.filter(user=user).count() == 1
        assert BudgetingPeriod.objects.filter(user=user).first() == active_period

    @pytest.mark.django_db(transaction=True)
    def test_error_is_active_none(self, user):
        """Test error on creating period with is_active set to None."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': None,
        }
        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert 'null value in column "is_active"' in str(exc.value)
        assert not BudgetingPeriod.objects.filter(user=user).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize('date_start, date_end', ((None, date.today()), (date.today(), None), (None, None)))
    def test_error_date_not_set(self, user, date_start: Union[date, None], date_end: Union[date, None]):
        """Test error on creating period with date_start or date_end set to None."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date_start,
            'date_end': date_end,
        }

        with pytest.raises(IntegrityError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert 'null value in column "date_' in str(exc.value)
        assert not BudgetingPeriod.objects.filter(user=user).exists()

    def test_error_date_end_before_date_start(self, user):
        """Test error on creating period with date_end earlier than date_start."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 5, 1),
            'date_end': date(2023, 4, 30),
        }

        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload)
        assert exc.value.code == 'date-invalid'
        assert exc.value.message == 'start_date: Start date should be earlier than end date.'
        assert not BudgetingPeriod.objects.filter(user=user).exists()

    @pytest.mark.parametrize(
        'date_start, date_end',
        (
            # Date start before first existing period
            (date(2023, 5, 1), date(2023, 6, 1)),
            (date(2023, 5, 1), date(2023, 6, 15)),
            (date(2023, 5, 1), date(2023, 6, 30)),
            (date(2023, 5, 1), date(2023, 7, 1)),
            (date(2023, 5, 1), date(2023, 7, 15)),
            (date(2023, 5, 1), date(2023, 7, 31)),
            (date(2023, 5, 1), date(2023, 8, 1)),
            # Date start same as in first existing period
            (date(2023, 6, 1), date(2023, 6, 15)),
            (date(2023, 6, 1), date(2023, 6, 30)),
            (date(2023, 6, 1), date(2023, 7, 1)),
            (date(2023, 6, 1), date(2023, 7, 15)),
            (date(2023, 6, 1), date(2023, 7, 31)),
            (date(2023, 6, 1), date(2023, 8, 1)),
            # Date start between first existing period daterange
            (date(2023, 6, 15), date(2023, 6, 30)),
            (date(2023, 6, 15), date(2023, 7, 1)),
            (date(2023, 6, 15), date(2023, 7, 15)),
            (date(2023, 6, 15), date(2023, 7, 31)),
            (date(2023, 6, 15), date(2023, 8, 1)),
            # Date start same as first existing period's end date
            (date(2023, 6, 30), date(2023, 7, 1)),
            (date(2023, 6, 30), date(2023, 7, 15)),
            (date(2023, 6, 30), date(2023, 7, 31)),
            (date(2023, 6, 30), date(2023, 8, 1)),
            # Date start same as in second existing period
            (date(2023, 7, 1), date(2023, 7, 15)),
            (date(2023, 7, 1), date(2023, 7, 31)),
            (date(2023, 7, 1), date(2023, 8, 1)),
            # Date start between second existing period daterange
            (date(2023, 7, 15), date(2023, 7, 31)),
            # Date start same as second existing period's end date
            (date(2023, 7, 31), date(2023, 8, 1)),
        ),
    )
    def test_error_date_invalid(self, user, date_start: date, date_end: date):
        """Test error on creating period with invalid dates."""
        payload_1 = {
            'name': '2023_06',
            'user': user,
            'date_start': date(2023, 6, 1),
            'date_end': date(2023, 6, 30),
        }
        payload_2 = {
            'name': '2023_07',
            'user': user,
            'date_start': date(2023, 7, 1),
            'date_end': date(2023, 7, 31),
        }
        payload_invalid = {
            'name': 'invalid',
            'user': user,
            'date_start': date_start,
            'date_end': date_end,
        }
        BudgetingPeriod.objects.create(**payload_1)
        BudgetingPeriod.objects.create(**payload_2)
        with pytest.raises(ValidationError) as exc:
            BudgetingPeriod.objects.create(**payload_invalid)
        assert exc.value.code == 'period-range-invalid'
        assert (
            exc.value.message == "date_start: Budgeting period date range collides with other user's budgeting periods."
        )
        assert BudgetingPeriod.objects.filter(user=user).count() == 2
