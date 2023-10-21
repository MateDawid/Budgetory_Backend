import datetime

import pytest
from periods.models import BudgetingPeriod


@pytest.mark.django_db
class TestBudgetingPeriodModel:
    """Tests for BudgetingPeriod model"""

    def test_create_first_period_successful(self, user):
        """Test creating first user BudgetingPeriod successfully."""
        payload = {
            'name': '2023_10',
            'user': user,
            'date_start': datetime.date(day=1, month=1, year=2023),
            'date_end': datetime.date(day=31, month=1, year=2023),
        }

        budgeting_period = BudgetingPeriod.objects.create(**payload)
        assert budgeting_period.name == payload['name']
        assert budgeting_period.user == payload['user']
        assert budgeting_period.date_start == payload['date_start']
        assert budgeting_period.date_end == payload['date_end']
        assert budgeting_period.is_active is False
        assert str(budgeting_period) == f'{budgeting_period.name} ({budgeting_period.user.email})'
