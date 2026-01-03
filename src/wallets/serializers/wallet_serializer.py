from rest_framework.serializers import ModelSerializer

from wallets.models import Wallet


class WalletSerializer(ModelSerializer):
    """Serializer for Wallet model."""

    class Meta:
        model = Wallet
        fields = ["id", "name", "description", "currency", "members"]
        read_only_fields = ["id"]
