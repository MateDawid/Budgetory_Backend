from django.contrib.auth import get_user_model
from periods.models import BudgetingPeriod
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BudgetingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BudgetingPeriod."""

    class Meta:
        model = BudgetingPeriod
        fields = ['id', 'user', 'name', 'date_start', 'date_end', 'is_active']
        read_only_fields = ['id']

    def validate_is_active(self, value: bool) -> bool:
        if value is True:
            user = get_user_model().objects.get(id=self.initial_data.get('user'))
            active_periods = user.budgeting_periods.filter(is_active=True).exclude(
                pk=getattr(self.instance, 'pk', None)
            )
            if active_periods.exists():
                raise ValidationError('User already has active budgeting period.', code='active-invalid')
        return value
