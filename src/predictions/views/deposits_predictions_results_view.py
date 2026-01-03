from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, Func, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToWalletPermission
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from periods.models import Period
from predictions.models import ExpensePrediction
from transfers.models import Expense, Transfer
from wallets.models import Wallet


def get_deposit_period_expenses(wallet_pk: int, period_pk: int) -> Func:
    """
    Function for calculate Transfers values sum in Period done by particular Deposit.

    Args:
        period_pk (int): Period id.
        wallet_pk (int): Wallet id.

    Returns:
        Func: ORM function returning Sum of Period Transfers values for specified Deposit.
    """
    return Coalesce(
        Subquery(
            Expense.objects.filter(period__wallet__pk=wallet_pk, period=period_pk, deposit__id=OuterRef("pk"))
            .values("period")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def get_deposit_period_expense_predictions(wallet_pk: int, period_pk: int) -> Func:
    """
    Function for calculate ExpensePredictions current_plan values sum in Period for particular Deposit.

    Args:
        period_pk (int): Period id.
        wallet_pk (int): Wallet id.

    Returns:
        Func: ORM function returning Sum of Period ExpensePredictions current_plan values
        for specified Deposit.
    """

    return Coalesce(
        Subquery(
            ExpensePrediction.objects.filter(
                period__wallet__pk=wallet_pk, period=period_pk, category__deposit__id=OuterRef("pk")
            )
            .values("period")
            .annotate(total=Sum("current_plan"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def sum_period_and_previous_transfers(wallet_pk: int, period_pk: int, category_type: CategoryType) -> Func:
    """
    Function for calculate Transfers sum of specified type from given and previous Periods
    for particular Deposit.

    Args:
        wallet_pk (int): Wallet id.
        period_pk (int): Period id.
        category_type (CategoryType): Category type, like 'Income' or 'Expense'.

    Returns:
        Func: ORM function returning Sum of Period Transfers (Incomes or Expenses) values for specified Deposit
        from given and previous Periods.
    """
    return Coalesce(
        Subquery(
            Transfer.objects.filter(
                period__wallet__pk=wallet_pk,
                transfer_type=category_type,
                period__date_start__lt=Subquery(
                    Period.objects.filter(pk=period_pk).values(
                        "date_start" if category_type == CategoryType.EXPENSE else "date_end"
                    )[:1]
                ),
                deposit__id=OuterRef("pk"),
            )
            .values("transfer_type")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def get_deposit_period_balance() -> Func:
    """
    Function for calculate ExpensePredictions current_plan values sum in Period for particular Deposit.

    Returns:
        Func: ORM function returning Sum of Period ExpensePredictions current_plan values
        for specified Deposit.
    """

    return Coalesce(
        F("incomes_sum") - F("expenses_sum"), Value(Decimal("0.00")), output_field=DecimalField(decimal_places=2)
    )


def get_funds_left_for_predictions() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in particular Period.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in particular Period.
    """
    return ExpressionWrapper(F("period_balance") - F("predictions_sum"), output_field=DecimalField(decimal_places=2))


def get_funds_left_for_expenses() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in particular Period.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in particular Period.
    """
    return ExpressionWrapper(F("predictions_sum") - F("period_expenses"), output_field=DecimalField(decimal_places=2))


class DepositsPredictionsResultsAPIView(APIView):
    """
    View returning Deposits results in indicated Period - predictions, planned expenses and actual expenses.
    """

    choices = CategoryPriority.choices
    permission_classes = (
        IsAuthenticated,
        UserBelongsToWalletPermission,
    )

    def get(self, request: Request, wallet_pk: int, period_pk: int) -> Response:
        """
        Returns serialized DepositResults in particular Period.

        Args:
            request [Request]: Deposit request.

        Returns:
            Response: Serialized DepositResults in particular Period.
        """
        if not Period.objects.filter(wallet_id=wallet_pk, pk=period_pk).exists():
            raise NotFound("Period with given pk does not exist in Wallet.")
        deposits = (
            Wallet.objects.get(pk=wallet_pk)
            .entities.filter(is_deposit=True)
            .annotate(
                predictions_sum=get_deposit_period_expense_predictions(wallet_pk, period_pk),
                incomes_sum=sum_period_and_previous_transfers(wallet_pk, period_pk, CategoryType.INCOME),
                expenses_sum=sum_period_and_previous_transfers(wallet_pk, period_pk, CategoryType.EXPENSE),
            )
            .annotate(
                period_expenses=get_deposit_period_expenses(wallet_pk, period_pk),
                period_balance=get_deposit_period_balance(),
            )
            .annotate(
                funds_left_for_predictions=get_funds_left_for_predictions(),
                funds_left_for_expenses=get_funds_left_for_expenses(),
            )
            .values(
                "id",
                "name",
                "period_expenses",
                "predictions_sum",
                "period_balance",
                "funds_left_for_predictions",
                "funds_left_for_expenses",
            )
        )

        return Response(
            [
                {
                    "deposit_name": deposit["name"],
                    "predictions_sum": f"{Decimal(str(deposit['predictions_sum'])):.2f}",
                    "period_balance": f"{Decimal(str(deposit['period_balance'])):.2f}",
                    "period_expenses": f"{Decimal(str(deposit['period_expenses'])):.2f}",
                    "funds_left_for_predictions": f"{Decimal(str(deposit['funds_left_for_predictions'])):.2f}",
                    "funds_left_for_expenses": f"{Decimal(str(deposit['funds_left_for_expenses'])):.2f}",
                }
                for deposit in deposits.order_by("id")
            ]
        )
