from budgets.models import Budget, BudgetingPeriod
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class BudgetSerializer(serializers.ModelSerializer):
    """Serializer for Budget model."""

    class Meta:
        model = Budget
        fields = ['id', 'name', 'description', 'currency', 'members']
        read_only_fields = ['id']


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

    def validate(self, attrs):
        """Validates date_start and date_end by checking they are in proper order or if any colliding periods exist."""
        date_start = attrs.get('date_start', getattr(self.instance, 'date_start', None))
        date_end = attrs.get('date_end', getattr(self.instance, 'date_end', None))
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
        return super().validate(attrs)
