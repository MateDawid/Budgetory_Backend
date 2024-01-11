import datetime
from typing import Union

from django.db.models import Q
from periods.models import BudgetingPeriod
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BudgetingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BudgetingPeriod."""

    class Meta:
        model = BudgetingPeriod
        fields = ['id', 'name', 'date_start', 'date_end', 'is_active']
        read_only_fields = ['id']

    def validate_name(self, value: str) -> str:
        """Checks if user has not used passed name for period already."""
        try:
            self.Meta.model.objects.get(user=self.context['request'].user, name=value)
        except self.Meta.model.DoesNotExist:
            pass
        else:
            raise serializers.ValidationError(f'Users period with name {value} already exists.')
        return value

    def validate_is_active(self, value: bool) -> bool:
        """Validates is_active param by checking if any other period is not marked as active already."""
        if value is True:
            active_periods = (
                self.context['request']
                .user.budgeting_periods.filter(is_active=True)
                .exclude(pk=getattr(self.instance, 'pk', None))
            )
            if active_periods.exists():
                raise ValidationError('User already has active budgeting period.')
        return value

    def validate_date_start(self, date_start: datetime.date) -> Union[datetime.date, None]:
        """Validates date_start and date_end by checking they are in proper order or if any colliding periods exist."""
        date_start = self._get_date(date_start)
        date_end = self._get_date(self.initial_data['date_end'])
        if date_start is None or date_end is None:
            return date_start
        if date_start >= date_end:
            raise ValidationError('Start date should be earlier than end date.')
        if (
            self.context['request']
            .user.budgeting_periods.filter(
                Q(date_start__lte=date_start, date_end__gte=date_start)
                | Q(date_start__lte=date_end, date_end__gte=date_end)
                | Q(date_start__gte=date_start, date_end__lte=date_end)
            )
            .exclude(pk=getattr(self.instance, 'pk', None))
            .exists()
        ):
            raise ValidationError("Budgeting period date range collides with other user's budgeting periods.")
        return date_start

    def _get_date(self, input_date: Union[str, datetime.date]) -> datetime.date:
        """Used to make sure, that date validation operates on date objects."""
        if isinstance(input_date, datetime.date):
            return input_date
        else:
            return datetime.datetime.strptime(input_date, '%Y-%m-%d').date()
