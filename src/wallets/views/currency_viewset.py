from rest_framework.mixins import ListModelMixin
from rest_framework.viewsets import GenericViewSet

from wallets.models import Currency
from wallets.serializers.currency_serializer import CurrencySerializer


class CurrencyViewSet(ListModelMixin, GenericViewSet):
    """View for retrieving list Currencies."""

    serializer_class = CurrencySerializer
    queryset = Currency.objects.all().order_by("name")
    permission_classes = []
