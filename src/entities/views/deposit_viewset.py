from decimal import Decimal

from django.db import transaction
from django.db.models import Case, DecimalField, F, Func, OuterRef, Q, QuerySet, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.models.choices.category_type import CategoryType
from entities.filtersets.deposit_filterset import DepositFilterSet
from entities.models.deposit_model import Deposit
from entities.serializers.deposit_serializer import DepositSerializer
from periods.models import Period
from predictions.models import ExpensePrediction
from transfers.models import Transfer


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
            Transfer.objects.filter(transfer_type=transfer_type, period__wallet__pk=OuterRef("wallet__pk"))
            .values("period__wallet")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def sum_deposit_transfers(transfer_type: CategoryType) -> Func:
    """
    Function for calculate Transfers values sum of given CategoryType for Deposit.

    Args:
        transfer_type (CategoryType): Transfer type - INCOME or EXPENSE

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values for specified CategoryType.
    """
    return Coalesce(
        Sum(
            "deposit_transfers__value",
            filter=Q(deposit_transfers__transfer_type=transfer_type),
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def get_wallet_balance() -> Func:
    """
    Function for calculate Transfers values sum for Wallet.

    Returns:
        Func: ORM function returning Sum of Wallet Transfers values.
    """
    return Coalesce(
        F("wallet_incomes_sum") - F("wallet_expenses_sum"), Value(0), output_field=DecimalField(decimal_places=2)
    )


def get_deposit_balance() -> Func:
    """
    Function for calculate Transfers values sum for Deposit.

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values.
    """
    return Coalesce(
        F("deposit_incomes_sum") - F("deposit_expenses_sum"), Value(0), output_field=DecimalField(decimal_places=2)
    )


def get_wallet_percentage() -> Case:
    """
    Function for calculate percentage of Deposit balance in Wallet balance.

    Handles division by zero by checking if wallet_balance is zero before dividing.

    Returns:
        Case: ORM Case expression returning percentage of Deposit in Wallet balance or 0 if wallet balance is zero.
    """
    return Case(
        When(Q(wallet_balance=0), then=Value(Decimal("0.00"))),
        default=F("balance") / F("wallet_balance") * 100,
        output_field=DecimalField(decimal_places=2),
    )


class DepositViewSet(ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToWalletPermission]
    filterset_class = DepositFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "balance")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Deposits for Wallet passed in URL and annotate them with sum of Transfers.

        Conditionally extends QuerySet with Transfers sums and balances if needed.

        Returns:
            QuerySet: Filtered Deposit QuerySet.
        """
        qs = self.queryset.filter(wallet__pk=self.kwargs.get("wallet_pk")).distinct()
        fields = self.request.query_params.get("fields", "").split(",")
        if any(key in fields for key in ("balance", "wallet_balance", "wallet_percentage")):
            qs = qs.annotate(
                deposit_incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                deposit_expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            ).annotate(
                balance=get_deposit_balance(),
            )
        if any(key in fields for key in ("wallet_balance", "wallet_percentage")):
            qs = qs.annotate(
                wallet_incomes_sum=get_wallet_transfers_sum(CategoryType.INCOME),
                wallet_expenses_sum=get_wallet_transfers_sum(CategoryType.EXPENSE),
            ).annotate(
                wallet_balance=get_wallet_balance(),
            )
        if "wallet_percentage" in fields:
            qs = qs.annotate(wallet_percentage=get_wallet_percentage())
        return qs

    def perform_create(self, serializer: DepositSerializer) -> None:
        """
        Additionally save Wallet from URL on Deposit instance during saving serializer. Create Entity object for
        Deposit representation in Transfers. Creates initial Categories for Deposit.

        Args:
            serializer [DepositSerializer]: Serializer for Deposit model.
        """
        wallet_pk = self.kwargs.get("wallet_pk")
        with transaction.atomic():
            deposit = serializer.save(wallet_id=wallet_pk, is_deposit=True)
            ExpensePrediction.objects.bulk_create(
                ExpensePrediction(
                    deposit_id=deposit.pk,
                    category=None,
                    period_id=period_id,
                    initial_plan=Decimal("0.00"),
                    current_plan=Decimal("0.00"),
                )
                for period_id in Period.objects.filter(wallet_id=wallet_pk).values_list("id", flat=True)
            )
