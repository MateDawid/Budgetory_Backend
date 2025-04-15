from rest_framework import serializers

from entities.models.deposit_model import Deposit
from entities.serializers.entity_serializer import EntitySerializer


class DepositSerializer(EntitySerializer):
    """Serializer for Deposit."""

    balance = serializers.DecimalField(max_digits=20, decimal_places=2, default=0)

    class Meta:
        model = Deposit
        fields = ["id", "name", "description", "is_active", "balance"]
        read_only_fields = ["id"]
