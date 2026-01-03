from django.db import transaction
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_users.serializers.user_serializer import UserSerializer
from wallets.filtersets.wallet_filterset import WalletFilterSet
from wallets.models import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer


class WalletViewSet(ModelViewSet):
    """View for manage Wallets."""

    serializer_class = WalletSerializer
    queryset = Wallet.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = WalletFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = (
        "id",
        "name",
    )

    def get_queryset(self) -> QuerySet:
        """
        Retrieves Wallets membered by authenticated User.

        Returns:
            QuerySet: QuerySet containing Wallets containing authenticated User as member.
        """
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            return self.queryset.filter(members=user).order_by("id").distinct()
        return self.queryset.none()  # pragma: no cover

    @action(detail=True, methods=["GET"])
    def members(self, request: Request, **kwargs: dict) -> Response:
        """
        Endpoint returning members list of particular Wallet.

        Args:
            request [Request]: User request.
            kwargs [dict]: Keyword arguments.

        Returns:
            Response: HTTP response with particular Wallet members list.
        """
        wallet = get_object_or_404(self.queryset.model, pk=kwargs.get("pk"))
        serializer = UserSerializer(wallet.members.all(), many=True)
        return Response(serializer.data)

    def perform_create(self, serializer: WalletSerializer) -> None:
        """
        Adds request User as a member of Wallet model.

        Args:
            serializer [WalletSerializer]: Wallet data serializer.
        """
        with transaction.atomic():
            wallet = serializer.save()
            wallet.members.add(self.request.user)
