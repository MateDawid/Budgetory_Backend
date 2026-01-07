from decimal import Decimal

from django.db import transaction
from django.db.models import Count, DecimalField, F, Func, OuterRef, QuerySet, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_users.serializers.user_serializer import UserSerializer
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from transfers.models import Transfer
from wallets.filtersets.wallet_filterset import WalletFilterSet
from wallets.models import Wallet
from wallets.serializers.wallet_serializer import WalletSerializer


def get_wallet_transfers_sum(transfer_type: CategoryType) -> Func:
    """
    Function for calculate Transfers values sum in Wallet.

    Args:
        transfer_type (CategoryType): Transfer type.

    Returns:
        Func: ORM function returning Sum of Wallet Transfers values for specified Transfer Type.
    """
    return Coalesce(
        Subquery(
            Transfer.objects.filter(transfer_type=transfer_type, period__wallet__pk=OuterRef("pk"))
            .values("period__wallet")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def get_wallet_balance() -> Func:
    """
    Function for calculate Transfers values sum for Deposit.

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values.
    """
    return Coalesce(F("incomes_sum") - F("expenses_sum"), Value(0), output_field=DecimalField(decimal_places=2))


def get_wallet_deposits_count() -> Func:
    """
    Function for get number of Wallet Deposits.

    Returns:
        Func: ORM function returning number of Wallet Deposits.
    """
    return Coalesce(
        Subquery(
            Deposit.objects.filter(wallet__pk=OuterRef("pk"))
            .values("wallet")
            .annotate(total=Count("id"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=0),
        ),
        Value(Decimal("0")),
        output_field=DecimalField(decimal_places=0),
    )


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
            return (
                self.queryset.filter(members=user)
                .order_by("id")
                .distinct()
                .annotate(
                    incomes_sum=get_wallet_transfers_sum(CategoryType.INCOME),
                    expenses_sum=get_wallet_transfers_sum(CategoryType.EXPENSE),
                )
                .annotate(balance=get_wallet_balance(), deposits_count=get_wallet_deposits_count())
            )
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
