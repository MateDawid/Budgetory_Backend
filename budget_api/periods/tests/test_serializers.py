from datetime import date

import pytest
from periods.models import BudgetingPeriod
from periods.serializers import BudgetingPeriodSerializer


def check_period_validated_data(serializer, payload):
    """Helper method for checking BudgetingPeriod validated data."""
    for key in serializer.validated_data:
        if key == 'user':
            assert getattr(serializer.validated_data[key], 'id') == payload[key]
        else:
            assert serializer.validated_data[key] == payload[key]


@pytest.mark.django_db
class TestBudgetingPeriodSerializer:
    """Tests for BudgetingPeriodSerializer."""

    def test_save_valid_budgeting_period(self, user):
        """Test for successful saving data in serializer."""
        payload = {
            'name': '2023_01',
            'user': user.id,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        serializer = BudgetingPeriodSerializer(data=payload)
        assert serializer.is_valid(raise_exception=True)
        check_period_validated_data(serializer, payload)
        serializer.save()
        assert BudgetingPeriod.objects.filter(user=user).count() == 1

    def test_save_two_valid_budgeting_periods(self, user):
        """Test for successful creating two periods for same user using serializer."""
        payload_1 = {
            'name': '2023_01',
            'user': user.id,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        payload_2 = {
            'name': '2023_02',
            'user': user.id,
            'date_start': date(2023, 2, 1),
            'date_end': date(2023, 2, 28),
        }
        serializer_1, serializer_2 = BudgetingPeriodSerializer(data=payload_1), BudgetingPeriodSerializer(
            data=payload_2
        )
        assert serializer_1.is_valid(raise_exception=True)
        assert serializer_2.is_valid(raise_exception=True)
        for serializer, payload in [(serializer_1, payload_1), (serializer_2, payload_2)]:
            check_period_validated_data(serializer, payload)
            serializer.save()
        assert BudgetingPeriod.objects.filter(user=user).count() == 2

    def test_save_same_period_by_two_users(self, user_factory):
        """Test creating period with the same params by two users using serializer"""
        payload_1 = {
            'name': '2023_01',
            'user': user_factory().id,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }
        payload_2 = {
            'name': '2023_01',
            'user': user_factory().id,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
            'is_active': True,
        }

        serializer_1, serializer_2 = BudgetingPeriodSerializer(data=payload_1), BudgetingPeriodSerializer(
            data=payload_2
        )
        assert serializer_1.is_valid(raise_exception=True)
        assert serializer_2.is_valid(raise_exception=True)
        for serializer, payload in [(serializer_1, payload_1), (serializer_2, payload_2)]:
            check_period_validated_data(serializer, payload)
            serializer.save()
        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=payload_1['user']).count() == 1
        assert BudgetingPeriod.objects.filter(user=payload_2['user']).count() == 1
