from rest_framework import serializers

from entities.models.deposit_model import Deposit
from entities.serializers.entity_serializer import EntitySerializer


class DepositSerializer(EntitySerializer):
    """Serializer for Deposit."""

    balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    wallet_balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    wallet_percentage = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)

    class Meta:
        model = Deposit
        fields = [
            "id",
            "name",
            "description",
            "is_active",
            "value",
            "label",
            "balance",
            "wallet_balance",
            "wallet_percentage",
        ]
        read_only_fields = ["id", "value", "label", "balance", "wallet_percentage"]
