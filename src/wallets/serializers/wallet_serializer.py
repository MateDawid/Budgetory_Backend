from typing import OrderedDict

from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, DecimalField

from wallets.models import Wallet


class WalletSerializer(FlexFieldsModelSerializer):
    """Serializer for Wallet model."""

    currency_name = CharField(source="currency.name", read_only=True)
    balance = DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    deposits_count = DecimalField(max_digits=20, decimal_places=0, default=0, read_only=True)

    class Meta:
        model = Wallet
        fields = ["id", "name", "description", "currency", "currency_name", "balance", "deposits_count"]
        read_only_fields = ["id", "balance", "deposits_count", "currency_name"]

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
