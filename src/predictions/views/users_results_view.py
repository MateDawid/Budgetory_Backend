from decimal import Decimal

from django.db.models import CharField, DecimalField, ExpressionWrapper, F, Func, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import Budget, BudgetingPeriod
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from entities.models.choices.deposit_type import DepositType
from predictions.models import ExpensePrediction
from transfers.models import Expense, Transfer


def get_owner_filter(param_name: str, is_common_user: bool) -> dict:
    """
    Returns category filter depending on type of TransferCategory User.

    Args:
        param_name (str): Name of param, from which owner will be collected, like 'deposit' and 'category'.
        is_common_user (bool): Indicates if TransferCategory is owned by particular
        User or is common one (without User assigned).

    Returns:
        dict: Filters for QuerySet.
    """
    return {f"{param_name}__owner__isnull": True} if is_common_user else {f"{param_name}__owner__pk": OuterRef("pk")}


def get_user_period_expenses(budget_pk: int, period_pk: int, is_common_user: bool = False) -> Func:
    """
    Function for calculate Transfers values sum in BudgetingPeriod done by particular User.

    Args:
        period_pk (int): Period id.
        budget_pk (int): Budget id.
        is_common_user (bool): Indicates if TransferCategory is owned by particular
        User or is common one (without User assigned).

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers values for specified User.
    """
    return Coalesce(
        Subquery(
            Expense.objects.filter(
                period__budget__pk=budget_pk,
                period=period_pk,
                deposit__deposit_type=DepositType.DAILY_EXPENSES,
                **get_owner_filter("deposit", is_common_user),
            )
            .values("period")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def get_user_period_expense_predictions(budget_pk: int, period_pk: int, is_common_user: bool = False) -> Func:
    """
    Function for calculate ExpensePredictions current_plan values sum in BudgetingPeriod for particular User.

    Args:
        period_pk (int): Period id.
        budget_pk (int): Budget id.
        is_common_user (bool): Indicates if TransferCategory is owned by particular
        User or is common one (without User assigned).

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod ExpensePredictions current_plan values for specified User.
    """

    return Coalesce(
        Subquery(
            ExpensePrediction.objects.filter(
                period__budget__pk=budget_pk, period=period_pk, **get_owner_filter("category", is_common_user)
            )
            .values("period")
            .annotate(total=Sum("current_plan"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def sum_period_and_previous_transfers(
    budget_pk: int, period_pk: int, category_type: CategoryType, is_common_user: bool = False
) -> Func:
    """
    Function for calculate Transfers sum of specified type from given and previous BudgetingPeriods for particular User.

    Args:
        budget_pk (int): Budget id.
        period_pk (int): Period id.
        category_type (CategoryType): Category type, like 'Income' or 'Expense'.
        is_common_user (bool): Indicates if TransferCategory is owned by particular
        User or is common one (without User assigned).

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod Transfers (Incomes or Expenses) values for specified User
        from given and previous BudgetingPeriods.
    """
    return Coalesce(
        Subquery(
            Transfer.objects.filter(
                period__budget__pk=budget_pk,
                category__category_type=category_type,
                period__date_start__lt=Subquery(
                    BudgetingPeriod.objects.filter(pk=period_pk).values(
                        "date_start" if category_type == CategoryType.EXPENSE else "date_end"
                    )[:1]
                ),
                deposit__deposit_type=DepositType.DAILY_EXPENSES,
                **get_owner_filter("deposit", is_common_user),
            )
            .values("category__category_type")
            .annotate(total=Sum("value"))
            .values("total")[:1],
            output_field=DecimalField(decimal_places=2),
        ),
        Value(Decimal("0.00")),
        output_field=DecimalField(decimal_places=2),
    )


def get_user_period_balance() -> Func:
    """
    Function for calculate ExpensePredictions current_plan values sum in BudgetingPeriod for particular User.

    Returns:
        Func: ORM function returning Sum of BudgetingPeriod ExpensePredictions current_plan values for specified User.
    """

    return Coalesce(
        F("incomes_sum") - F("expenses_sum"), Value(Decimal("0.00")), output_field=DecimalField(decimal_places=2)
    )


def get_funds_left_for_predictions() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in particular BudgetingPeriod.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in particular BudgetingPeriod.
    """
    return ExpressionWrapper(F("period_balance") - F("predictions_sum"), output_field=DecimalField(decimal_places=2))


def get_funds_left_for_expenses() -> ExpressionWrapper:
    """
    Function for calculate funds left for given TransferCategory in particular BudgetingPeriod.

    Returns:
        ExpressionWrapper: ORM function returning calculating funds left for specified
        TransferCategory in particular BudgetingPeriod.
    """
    return ExpressionWrapper(F("predictions_sum") - F("period_expenses"), output_field=DecimalField(decimal_places=2))


class UsersResultsAPIView(APIView):
    """
    View returning Users results in indicated Period - predictions, planned expenses and actual expenses.
    """

    choices = CategoryPriority.choices
    permission_classes = (
        IsAuthenticated,
        UserBelongsToBudgetPermission,
    )

    def get(self, request: Request, budget_pk: int, period_pk: int) -> Response:
        """
        Returns serialized UserResults in particular BudgetingPeriod.

        Args:
            request [Request]: User request.

        Returns:
            Response: Serialized UserResults in particular BudgetingPeriod.
        """
        budget_members = (
            Budget.objects.get(pk=budget_pk)
            .members.all()
            .annotate(
                predictions_sum=get_user_period_expense_predictions(budget_pk, period_pk),
                incomes_sum=sum_period_and_previous_transfers(budget_pk, period_pk, CategoryType.INCOME),
                expenses_sum=sum_period_and_previous_transfers(budget_pk, period_pk, CategoryType.EXPENSE),
            )
            .annotate(
                period_expenses=get_user_period_expenses(budget_pk, period_pk),
                period_balance=get_user_period_balance(),
            )
            .annotate(
                funds_left_for_predictions=get_funds_left_for_predictions(),
                funds_left_for_expenses=get_funds_left_for_expenses(),
            )
            .values(
                "id",
                "username",
                "period_expenses",
                "predictions_sum",
                "period_balance",
                "funds_left_for_predictions",
                "funds_left_for_expenses",
            )
        )

        none_user_queryset = (
            Budget.objects.filter(pk=budget_pk)
            .extra(select={"id": "0"})
            .annotate(
                username=Value("🏦 Common", output_field=CharField()),
                predictions_sum=get_user_period_expense_predictions(budget_pk, period_pk, is_common_user=True),
                incomes_sum=sum_period_and_previous_transfers(
                    budget_pk, period_pk, CategoryType.INCOME, is_common_user=True
                ),
                expenses_sum=sum_period_and_previous_transfers(
                    budget_pk, period_pk, CategoryType.EXPENSE, is_common_user=True
                ),
            )
            .annotate(
                period_expenses=get_user_period_expenses(budget_pk, period_pk, is_common_user=True),
                period_balance=get_user_period_balance(),
            )
            .annotate(
                funds_left_for_predictions=get_funds_left_for_predictions(),
                funds_left_for_expenses=get_funds_left_for_expenses(),
            )
            .values(
                "id",
                "username",
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
                    "user_username": member["username"],
                    "predictions_sum": f"{Decimal(str(member['predictions_sum'])):.2f}",
                    "period_balance": f"{Decimal(str(member['period_balance'])):.2f}",
                    "period_expenses": f"{Decimal(str(member['period_expenses'])):.2f}",
                    "funds_left_for_predictions": f"{Decimal(str(member['funds_left_for_predictions'])):.2f}",
                    "funds_left_for_expenses": f"{Decimal(str(member['funds_left_for_expenses'])):.2f}",
                }
                for member in budget_members.union(none_user_queryset).order_by("id")
            ]
        )
