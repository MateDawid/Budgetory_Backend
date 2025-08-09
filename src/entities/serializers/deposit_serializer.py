import copy
from collections import OrderedDict

from rest_framework import serializers

from entities.models.choices.deposit_type import DepositType
from entities.models.deposit_model import Deposit
from entities.serializers.entity_serializer import EntitySerializer


class DepositSerializer(EntitySerializer):
    """Serializer for Deposit."""

    incomes_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    expenses_sum = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)

    class Meta:
        model = Deposit
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "deposit_type",
            "owner",
            "incomes_sum",
            "expenses_sum",
            "balance",
        ]
        read_only_fields = ["id", "incomes_sum", "expenses_sum", "balance"]

    def to_internal_value(self, data: OrderedDict) -> OrderedDict:
        """
        Additionally handles "-1" value for owner sent by Frontend in case of selecting None owner value.

        Attributes:
            data [dict]: Input data.

        Returns:
            dict: Dictionary containing overridden values.
        """
        updated_data = copy.deepcopy(data)
        if str(updated_data.get("owner")) == "-1":
            updated_data["owner"] = None
        return super().to_internal_value(updated_data)

    def to_representation(self, instance: Deposit) -> OrderedDict:
        """
        Extends model representation with "deposit_type_display" field for Frontend purposes.

        Attributes:
            instance [Deposit]: Deposit model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["owner_display"] = getattr(instance, "owner_display", "🏦 Common")  # noqa
        representation["deposit_type_display"] = DepositType(representation["deposit_type"]).label
        return representation
