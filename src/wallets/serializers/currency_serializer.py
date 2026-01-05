from rest_framework.serializers import ModelSerializer

from wallets.models import Currency


class CurrencySerializer(ModelSerializer):
    """Serializer for Wallet model."""

    class Meta:
        model = Currency
        fields = ["id", "name"]
