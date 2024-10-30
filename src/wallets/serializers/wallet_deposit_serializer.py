from decimal import Decimal

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from wallets.models.wallet_deposit_model import WalletDeposit


class WalletDepositSerializer(serializers.ModelSerializer):
    """Serializer for WalletDeposit model."""

    class Meta:
        model: Model = WalletDeposit
        fields = ("id", "deposit", "planned_weight")
        read_only_fields = ("id",)

    @staticmethod
    def validate_planned_weight(planned_weight: Decimal) -> Decimal:
        """
        Checks if planned_weight value is in acceptable range.

        Args:
            planned_weight (Decimal): Input planned_weight value.

        Returns:
            Decimal: Validated planned_weight value.
        """
        if not (Decimal("0.00") < planned_weight < Decimal("100.00")):
            raise ValidationError("Invalid value for planned_weight.")
        return planned_weight
