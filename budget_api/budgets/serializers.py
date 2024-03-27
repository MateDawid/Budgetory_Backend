from collections import OrderedDict

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

    def validate_name(self, value: str) -> str:
        """Checks if user has not used passed name for period already."""
        try:
            self.Meta.model.objects.get(owner=self.context['request'].user, name=value)
        except self.Meta.model.DoesNotExist:
            pass
        else:
            raise serializers.ValidationError(f'User already owns Budget with name "{value}".')
        return value


class BudgetingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BudgetingPeriod."""

    budget: Budget

    class Meta:
        model = BudgetingPeriod
        fields = ['id', 'name', 'date_start', 'date_end', 'is_active']
        read_only_fields = ['id']

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates name, is_active, date_start and date_end in separate methods.

        Args:
            attrs [OrderedDict]: Dictionary containing given BudgetingPeriod params.

        Returns:
            OrderedDict: Dictionary containing validated BudgetingPeriod params.
        """
        self.budget = self._get_budget()
        self._validate_name(attrs)
        self._validate_is_active(attrs)
        self._validate_dates(attrs)
        return attrs

    def _get_budget(self) -> Budget:
        """
        Returns Budget object indicated by its id in request URL.

        Returns:
            Budget: Budget model instance.

        Raises:
            ValidationError: Raised when Budget with given id not exists in database.
        """
        budget_pk = self.context['request'].parser_context.get('kwargs', {}).get('budget_pk')
        try:
            budget = Budget.objects.get(id=budget_pk)
        except Budget.DoesNotExist:
            raise ValidationError(f'Budget with pk "{budget_pk}" does not exist.')
        return budget

    def _validate_name(self, attrs: OrderedDict) -> None:
        """
        Checks if Budget contains BudgetingPeriod with given name already.

        Args:
            attrs [OrderedDict]: Dictionary containing given BudgetingPeriod params

        Raises:
            ValidationError: Raised when BudgetingPeriod for Budget with given name already exists in database.
        """
        name = attrs.get('name')
        try:
            self.Meta.model.objects.get(budget=self.budget, name=name)
        except self.Meta.model.DoesNotExist:
            pass
        else:
            raise ValidationError(f'Period with name "{name}" already exists in Budget.')

    def _validate_is_active(self, attrs: OrderedDict) -> None:
        """
        Checks if Budget contains active BudgetingPeriod.

        Args:
            attrs [OrderedDict]: Dictionary containing given BudgetingPeriod params

        Raises:
            ValidationError: Raised when active BudgetingPeriod for Budget already exists in database.
        """
        is_active = attrs.get('is_active')
        if is_active is True:
            active_periods = self.budget.periods.filter(is_active=True).exclude(pk=getattr(self.instance, 'pk', None))
            if active_periods.exists():
                raise ValidationError('Active period already exists in Budget.')

    def _validate_dates(self, attrs: OrderedDict) -> None:
        """
        Checks if given BudgetingPeriod start and end dates do not collide with other Budget periods dates.

        Args:
            attrs [OrderedDict]: Dictionary containing given BudgetingPeriod params

        Raises:
            ValidationError: Raised when date_end earlier than date start or some Budget periods
            dates collides with given dates.
        """
        date_start = attrs.get('date_start', getattr(self.instance, 'date_start', None))
        date_end = attrs.get('date_end', getattr(self.instance, 'date_end', None))
        if date_start >= date_end:
            raise ValidationError('Start date should be earlier than end date.')
        if (
            self.budget.periods.filter(
                Q(date_start__lte=date_start, date_end__gte=date_start)
                | Q(date_start__lte=date_end, date_end__gte=date_end)
                | Q(date_start__gte=date_start, date_end__lte=date_end)
            )
            .exclude(pk=getattr(self.instance, 'pk', None))
            .exists()
        ):
            raise ValidationError('Budgeting period date range collides with other period in Budget.')
        return super().validate(attrs)
