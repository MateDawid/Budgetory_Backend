from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from wallets.models.wallet_model import Wallet


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model."""

    class Meta:
        model: Model = Wallet
        fields = ("id", "name")
        read_only_fields = ("id",)

    def validate_name(self, name: str) -> str:
        """
        Checks if provided Wallet name was not used already in Budget.

        Args:
            name [str]: Input name of Wallet.

        Returns:
            str: Validated name of Wallet.
        """
        if self.Meta.model.objects.filter(budget__pk=self.context["view"].kwargs["budget_pk"], name=name).exists():
            raise ValidationError("Wallet name used already in Budget.")
        return name
