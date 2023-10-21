import datetime

import pytest
from periods.models import BudgetingPeriod


@pytest.mark.django_db
class TestBudgetingPeriodModel:
    """Tests for BudgetingPeriod model"""

    payload = {
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
            'date_start': datetime.date(day=1, month=2, year=2023),
            'date_end': datetime.date(day=28, month=2, year=2023),
            'user': user,
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
