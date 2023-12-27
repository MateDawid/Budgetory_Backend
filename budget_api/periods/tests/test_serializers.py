from datetime import date

import pytest
from periods.models import BudgetingPeriod
from periods.serializers import BudgetingPeriodSerializer
from rest_framework.exceptions import ValidationError


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
        """Test for successful saving BudgetingPeriodSerializer."""
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
        """Test for successful saving two BudgetingPeriodSerializers for the same user."""
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

        serializer_1 = BudgetingPeriodSerializer(data=payload_1)
        serializer_2 = BudgetingPeriodSerializer(data=payload_2)

        assert serializer_1.is_valid(raise_exception=True)
        assert serializer_2.is_valid(raise_exception=True)
        for serializer, payload in [(serializer_1, payload_1), (serializer_2, payload_2)]:
            check_period_validated_data(serializer, payload)
            serializer.save()
        assert BudgetingPeriod.objects.filter(user=user).count() == 2

    def test_save_same_period_by_two_users(self, user_factory):
        """Test saving BudgetingPeriodSerializer with the same params by two users."""
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

        serializer_1 = BudgetingPeriodSerializer(data=payload_1)
        serializer_2 = BudgetingPeriodSerializer(data=payload_2)

        assert serializer_1.is_valid(raise_exception=True)
        assert serializer_2.is_valid(raise_exception=True)
        for serializer, payload in [(serializer_1, payload_1), (serializer_2, payload_2)]:
            check_period_validated_data(serializer, payload)
            serializer.save()
        assert BudgetingPeriod.objects.all().count() == 2
        assert BudgetingPeriod.objects.filter(user=payload_1['user']).count() == 1
        assert BudgetingPeriod.objects.filter(user=payload_2['user']).count() == 1

    def test_error_name_too_long(self, user):
        """Test error on saving BudgetingPeriodSerializer with name too long."""
        max_length = BudgetingPeriodSerializer.Meta.model._meta.get_field('name').max_length
        payload = {
            'name': (max_length + 1) * 'a',
            'user': user.id,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }

        serializer = BudgetingPeriodSerializer(data=payload)

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert 'name' in exc.value.detail
        assert exc.value.detail['name'][0] == f'Ensure this field has no more than {max_length} characters.'

    def test_error_name_already_used(self, user):
        """Test error on saving BudgetingPeriodSerializer with already used name by the same user."""
        payload = {
            'name': '2023_01',
            'user': user,
            'date_start': date(2023, 1, 1),
            'date_end': date(2023, 1, 31),
        }
        BudgetingPeriod.objects.create(**payload)
        payload['user'] = payload['user'].id
        payload['date_start'] = date(2023, 2, 1)
        payload['date_end'] = date(2023, 2, 28)

        serializer = BudgetingPeriodSerializer(data=payload)

        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert 'non_field_errors' in exc.value.detail
        assert exc.value.detail['non_field_errors'][0] == 'The fields name, user must make a unique set.'
        assert BudgetingPeriod.objects.filter(user=user).count() == 1
