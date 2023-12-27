import datetime
from typing import Union

from django.contrib.auth import get_user_model
from django.db.models import Q
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
        """Validates is_active param by checking if any other period is not marked as active already."""
        if value is True:
            user = get_user_model().objects.get(id=self.initial_data.get('user'))
            active_periods = user.budgeting_periods.filter(is_active=True).exclude(
                pk=getattr(self.instance, 'pk', None)
            )
            if active_periods.exists():
                raise ValidationError('User already has active budgeting period.')
        return value

    def validate_date_start(self, date_start: datetime.date) -> Union[datetime.date, None]:
        """Validates date_start and date_end by checking they are in proper order or if any colliding periods exist."""
        date_end = self.initial_data['date_end']
        if date_start is None or date_end is None:
            return date_start
        user = get_user_model().objects.get(id=self.initial_data['user'])
        if date_start >= date_end:
            raise ValidationError('Start date should be earlier than end date.')
        if (
            user.budgeting_periods.filter(
                Q(date_start__lte=date_start, date_end__gte=date_start)
                | Q(date_start__lte=date_end, date_end__gte=date_end)
                | Q(date_start__gte=date_start, date_end__lte=date_end)
            )
            .exclude(pk=getattr(self.instance, 'pk', None))
            .exists()
        ):
            raise ValidationError("Budgeting period date range collides with other user's budgeting periods.")
        return date_start
