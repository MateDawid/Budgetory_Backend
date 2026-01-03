from decimal import Decimal

from django.db import transaction
from django.db.models import DecimalField, F, Func, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from periods.filtersets.period_filterset import PeriodFilterSet
from periods.models import Period
from periods.models.choices.period_status import PeriodStatus
from periods.serializers.period_serializer import PeriodSerializer
from predictions.models import ExpensePrediction


def sum_period_transfers(transfer_type: CategoryType) -> Func:
    """
    Function for calculate Transfers values sum of given CategoryType for Period.

    Args:
        transfer_type (CategoryType): Transfer type - INCOME or EXPENSE.

    Returns:
        Func: ORM function returning Sum of Period Transfers values for specified CategoryType.
    """
    return Coalesce(
        Sum(
            "transfers__value",
            filter=Q(transfers__transfer_type=transfer_type),
            output_field=DecimalField(decimal_places=2),
        ),
        Value(0),
        output_field=DecimalField(decimal_places=2),
    )


def prepare_predictions_on_period_activation(wallet_pk: str, period_pk: str) -> None:
    """
    Function for updating ExpensePrediction data on Period activation.

    Args:
        wallet_pk (str): Wallet ID.
        period_pk (str): Period ID.
    """
    if not all((wallet_pk, period_pk)):
        return
    # Set initial_value for predictions create by User
    ExpensePrediction.objects.filter(period__id=period_pk, initial_plan__isnull=True).update(
        initial_plan=F("current_plan")
    )
    # Create predictions with 0 value for not predicted categories
    predicted_categories_ids = ExpensePrediction.objects.filter(
        period__id=period_pk, period__wallet__id=wallet_pk, category__isnull=False
    ).values_list("category", flat=True)

    unpredicted_categories = TransferCategory.objects.filter(
        ~Q(id__in=predicted_categories_ids),
        category_type=CategoryType.EXPENSE,
    ).values_list("id", "deposit")

    zero_predictions = [
        ExpensePrediction(
            period_id=period_pk,
            deposit_id=deposit_id,
            category_id=category_id,
            initial_plan=Decimal("0.00"),
            current_plan=Decimal("0.00"),
        )
        for category_id, deposit_id in unpredicted_categories
    ]
    ExpensePrediction.objects.bulk_create(zero_predictions)


class PeriodViewSet(ModelViewSet):
    """View for manage Periods."""

    serializer_class = PeriodSerializer
    queryset = Period.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToWalletPermission]
    filterset_class = PeriodFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "status", "name", "date_start", "date_end", "incomes_sum", "expenses_sum")

    def get_queryset(self) -> QuerySet:
        """
        Retrieves Periods for Wallets to which authenticated User belongs.

        Returns:
            QuerySet: Filtered Period QuerySet.
        """
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            wallet_pk = self.kwargs.get("wallet_pk")
            if wallet_pk:
                return (
                    self.queryset.filter(wallet__members=user, wallet__pk=wallet_pk)
                    .order_by("-date_start")
                    .distinct()
                    .annotate(
                        incomes_sum=sum_period_transfers(CategoryType.INCOME),
                        expenses_sum=sum_period_transfers(CategoryType.EXPENSE),
                    )
                )
        return self.queryset.none()  # pragma: no cover

    def perform_create(self, serializer: PeriodSerializer) -> None:
        """
        Extended with saving Wallet in Period model.

        Args:
            serializer [PeriodSerializer]: Serializer for Period
        """
        wallet_pk = self.kwargs.get("wallet_pk")
        with transaction.atomic():
            period = serializer.save(wallet_id=wallet_pk)
            ExpensePrediction.objects.bulk_create(
                ExpensePrediction(
                    deposit_id=deposit_id,
                    category=None,
                    period_id=period.pk,
                    initial_plan=Decimal("0.00"),
                    current_plan=Decimal("0.00"),
                )
                for deposit_id in Deposit.objects.filter(wallet_id=wallet_pk).values_list("id", flat=True)
            )

    def update(self, request: Request, *args: list, **kwargs: dict) -> Response:
        """
        Method extended with updating periods ExpensePredictions initial_plan field on activating Period.

        Args:
            request (Request): User's request.
            *args (list): Additional arguments.
            **kwargs (dict): Keyword arguments.

        Returns:
            Response: Response object.
        """
        with transaction.atomic():
            if int(request.data.get("status", 0)) == PeriodStatus.ACTIVE.value:
                prepare_predictions_on_period_activation(
                    wallet_pk=kwargs.get("wallet_pk", "0"), period_pk=kwargs.get("pk", "0")
                )
            return super().update(request, *args, **kwargs)
