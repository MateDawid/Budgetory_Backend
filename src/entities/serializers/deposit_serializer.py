from rest_framework import serializers

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
            "incomes_sum",
            "expenses_sum",
            "balance",
        ]
        read_only_fields = ["id", "incomes_sum", "expenses_sum", "balance"]
