from typing import OrderedDict

from rest_framework.exceptions import ValidationError
from rest_framework.serializers import DecimalField, ModelSerializer

from wallets.models import Wallet


class WalletSerializer(ModelSerializer):
    """Serializer for Wallet model."""

    balance = DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    deposits_count = DecimalField(max_digits=20, decimal_places=0, default=0, read_only=True)

    class Meta:
        model = Wallet
        fields = ["id", "name", "description", "currency", "members", "balance", "deposits_count"]
        read_only_fields = ["id", "balance", "deposits_count"]

    def to_representation(self, instance: Wallet):
        """
        Updates instance representation with Wallet.currency field as Currency.name instead of Currency.id.

        Attributes:
            instance [Wallet]: Wallet model instance

        Returns:
            OrderedDict: Updated object representation.
        """
        representation = super().to_representation(instance)
        representation["currency_name"] = instance.currency.name
        return representation

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates if currency value is provided during creating new Wallet
        or updating currency value for existing Wallet.

        Args:
            attrs (OrderedDict): Provided object values.

        Returns:
            OrderedDict: Validated object values.

        Raises:
            ValidationError: Raised when currency value not provided during creating new Wallet
            or updating currency value for existing Wallet.
        """
        if (self.instance and "currency" in attrs and not attrs["currency"]) or (
            self.instance is None and not attrs.get("currency", None)
        ):
            raise ValidationError("Currency is required.")
        return attrs
