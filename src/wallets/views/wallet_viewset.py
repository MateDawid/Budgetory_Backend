from django.db.models import QuerySet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from wallets.models.wallet_model import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer


class WalletViewSet(ModelViewSet):
    """Base view for managing Wallets."""

    authentication_classes = [TokenAuthentication]
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    serializer_class = WalletSerializer

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Wallets for Budget passed in URL.

        Returns:
            QuerySet: Filtered Wallet QuerySet.
        """
        return Wallet.objects.filter(budget__pk=self.kwargs.get("budget_pk"))
