from rest_framework.serializers import CharField, IntegerField, ModelSerializer

from wallets.models import Currency


class CurrencySerializer(ModelSerializer):
    """Serializer for Wallet model."""

    value = IntegerField(source="id", read_only=True)
    label = CharField(source="name", read_only=True)

    class Meta:
        model = Currency
        fields = ["id", "name", "value", "label"]
