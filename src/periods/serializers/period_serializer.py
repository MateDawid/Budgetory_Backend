from collections import OrderedDict

from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from periods.models import Period
from periods.models.choices.period_status import PeriodStatus


class PeriodSerializer(serializers.ModelSerializer):
    """Serializer for Period."""

    status = serializers.IntegerField(default=PeriodStatus.DRAFT)
    incomes_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    expenses_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)

    class Meta:
        model = Period
        fields = ["id", "name", "status", "date_start", "date_end", "incomes_sum", "expenses_sum"]
        read_only_fields = ["id", "incomes_sum", "expenses_sum"]

    def validate_name(self, name: str) -> str:
        """
        Checks if Wallet contains Period with given name already.

        Args:
            name [str]: Given name for Period

        Returns:
            str: Validated name value.

        Raises:
            ValidationError: Raised when Period for Wallet with given name already exists in database.
        """
        if (
            Period.objects.filter(wallet=self.context["view"].kwargs["wallet_pk"], name=name)
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise ValidationError(f'Period with name "{name}" already exists in Wallet.')
        return name

    def validate_status(self, status: bool) -> bool:
        """
        Checks if Wallet contains active Period.

        Args:
            status [PeriodStatus]: Given status value to determine if Period is active or not.

        Returns:
            PeriodStatus: Validated status value.

        Raises:
            ValidationError: Raised when active Period for Wallet already exists in database.
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
            periods_in_status = Period.objects.filter(
                wallet__pk=self.context["view"].kwargs["wallet_pk"], status=status
            ).exclude(pk=getattr(self.instance, "pk", None))
            if periods_in_status.exists():
                raise ValidationError(f"{PeriodStatus(status).label} period already exists in Wallet.")
        return status

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Checks if given Period start and end dates do not collide with other Wallet periods dates.

        Args:
            attrs [OrderedDict]: Dictionary containing given Period params

        Returns:
            OrderedDict: Dictionary with validated attrs values.

        Raises:
            ValidationError: Raised when date_end earlier than date start or some Wallet periods
            dates collides with given dates.
        """
        date_start = attrs.get("date_start", getattr(self.instance, "date_start", None))
        date_end = attrs.get("date_end", getattr(self.instance, "date_end", None))
        if date_start >= date_end:
            raise ValidationError("Start date should be earlier than end date.")

        wallet_pk = self.context["view"].kwargs["wallet_pk"]

        colliding_periods = Period.objects.filter(
            Q(wallet__pk=wallet_pk, date_start__lte=date_start, date_end__gte=date_start)
            | Q(wallet__pk=wallet_pk, date_start__lte=date_end, date_end__gte=date_end)
            | Q(wallet__pk=wallet_pk, date_start__gte=date_start, date_end__lte=date_end)
        ).exclude(pk=getattr(self.instance, "pk", None))
        if colliding_periods.exists():
            raise ValidationError("Period date range collides with other period in Wallet.")

        if attrs.get("status", getattr(self.instance, "status", None)) == PeriodStatus.DRAFT:
            newer_periods = Period.objects.filter(wallet__pk=wallet_pk, date_start__gte=date_end).exclude(
                pk=getattr(self.instance, "pk", None)
            )
            if newer_periods.exists():
                raise ValidationError("New period date start has to be greater than previous period date end.")

        return super().validate(attrs)

    def to_representation(self, instance: Period) -> OrderedDict:
        """
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [Period]: Period model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["status_display"] = PeriodStatus(representation["status"]).label
        representation["value"] = instance.id
        representation["label"] = instance.name
        return representation
