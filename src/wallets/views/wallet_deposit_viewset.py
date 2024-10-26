from django.db.models import QuerySet
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from wallets.models.wallet_deposit_model import WalletDeposit
from wallets.serializers.wallet_deposit_serializer import WalletDepositSerializer


class WalletDepositViewSet(ModelViewSet):
    """Base view for managing WalletDeposits."""

    authentication_classes = [TokenAuthentication]
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )
    serializer_class = WalletDepositSerializer

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Wallets for Budget passed in URL.

        Returns:
            QuerySet: Filtered Wallet QuerySet.
        """
        return WalletDeposit.objects.filter(
            budget__pk=self.kwargs.get("budget_pk"), wallet__pk=self.kwargs.get("wallet_pk")
        )

    def perform_create(self, serializer: WalletDepositSerializer) -> None:
        """
        Additionally save Wallet from URL on WalletDeposit instance during saving serializer.

        Args:
            serializer [WalletSerializer]: Serializer for WalletDeposit model.
        """
        serializer.save(wallet_id=self.kwargs.get("wallet_pk"))
