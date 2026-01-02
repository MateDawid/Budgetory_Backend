from collections import OrderedDict

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from periods.models import BudgetingPeriod
from periods.models.choices.period_status import PeriodStatus


class BudgetingPeriodSerializer(serializers.ModelSerializer):
    """Serializer for BudgetingPeriod."""

    status = serializers.IntegerField(default=PeriodStatus.DRAFT)
    incomes_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    expenses_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)

    class Meta:
        model = BudgetingPeriod
        fields = ["id", "name", "status", "date_start", "date_end", "incomes_sum", "expenses_sum"]
        read_only_fields = ["id", "incomes_sum", "expenses_sum"]

    def validate_name(self, name: str) -> str:
        """
        Checks if Budget contains BudgetingPeriod with given name already.

        Args:
            name [str]: Given name for BudgetingPeriod

        Returns:
            str: Validated name value.

        Raises:
            ValidationError: Raised when BudgetingPeriod for Budget with given name already exists in database.
        """
        if (
            BudgetingPeriod.objects.filter(budget=self.context["view"].kwargs["budget_pk"], name=name)
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise ValidationError(f'Period with name "{name}" already exists in Budget.')
        return name

    def validate_status(self, status: bool) -> bool:
        """
        Checks if Budget contains active BudgetingPeriod.

        Args:
            status [PeriodStatus]: Given status value to determine if BudgetingPeriod is active or not.

        Returns:
            PeriodStatus: Validated status value.

        Raises:
            ValidationError: Raised when active BudgetingPeriod for Budget already exists in database.
        """
        if self.instance is None and status != PeriodStatus.DRAFT:
            raise ValidationError("New period has to be created with draft status.")
        elif (instance_status := getattr(self.instance, "status", None)) == PeriodStatus.CLOSED:
            raise ValidationError("Closed period cannot be changed.")
        elif instance_status == PeriodStatus.DRAFT and status == PeriodStatus.CLOSED:
            raise ValidationError("Draft period cannot be closed. It has to be active first.")
        elif instance_status == PeriodStatus.ACTIVE and status == PeriodStatus.DRAFT:
            raise ValidationError("Active period cannot be moved back to Draft status.")
        elif status in (PeriodStatus.ACTIVE, PeriodStatus.DRAFT):
            periods_in_status = BudgetingPeriod.objects.filter(
                budget__pk=self.context["view"].kwargs["budget_pk"], status=status
            ).exclude(pk=getattr(self.instance, "pk", None))
            if periods_in_status.exists():
                raise ValidationError(f"{PeriodStatus(status).label} period already exists in Budget.")
        return status

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Checks if given BudgetingPeriod start and end dates do not collide with other Budget periods dates.

        Args:
            attrs [OrderedDict]: Dictionary containing given BudgetingPeriod params

        Returns:
            OrderedDict: Dictionary with validated attrs values.

        Raises:
            ValidationError: Raised when date_end earlier than date start or some Budget periods
            dates collides with given dates.
        """
        date_start = attrs.get("date_start", getattr(self.instance, "date_start", None))
        date_end = attrs.get("date_end", getattr(self.instance, "date_end", None))
        if date_start >= date_end:
            raise ValidationError("Start date should be earlier than end date.")

        budget_pk = self.context["view"].kwargs["budget_pk"]

        colliding_periods = BudgetingPeriod.objects.filter(
            Q(budget__pk=budget_pk, date_start__lte=date_start, date_end__gte=date_start)
            | Q(budget__pk=budget_pk, date_start__lte=date_end, date_end__gte=date_end)
            | Q(budget__pk=budget_pk, date_start__gte=date_start, date_end__lte=date_end)
        ).exclude(pk=getattr(self.instance, "pk", None))
        if colliding_periods.exists():
            raise ValidationError("Budgeting period date range collides with other period in Budget.")

        if attrs.get("status", getattr(self.instance, "status", None)) == PeriodStatus.DRAFT:
            newer_periods = BudgetingPeriod.objects.filter(budget__pk=budget_pk, date_start__gte=date_end).exclude(
                pk=getattr(self.instance, "pk", None)
            )
            if newer_periods.exists():
                raise ValidationError("New period date start has to be greater than previous period date end.")

        return super().validate(attrs)

    def to_representation(self, instance: BudgetingPeriod) -> OrderedDict:
        """
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [BudgetingPeriod]: BudgetingPeriod model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["status_display"] = PeriodStatus(representation["status"]).label
        representation["value"] = instance.id
        representation["label"] = instance.name
        return representation
