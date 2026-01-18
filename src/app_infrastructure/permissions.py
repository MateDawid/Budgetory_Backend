from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class UserBelongsToWalletPermission(permissions.BasePermission):
    """Permission class for checking User access to Wallet."""

    message: str = "User does not have access to Wallet."

    def has_permission(self, request: Request, view: APIView) -> bool:
        """
        Checks if User is owner or member of Wallet passed in URL.

        Args:
            request [Request]: User request.
            view [APIView]: View on which request was made.

        Returns:
            bool: True if User is owner or member of Wallet, else False.
        """
        if request.method == "OPTIONS":  # pragma: no cover
            return request.user.is_authenticated
        wallet_pk = getattr(view, "kwargs", {}).get("wallet_pk")
        return request.user.is_wallet_member(wallet_pk)
