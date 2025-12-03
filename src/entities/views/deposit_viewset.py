from decimal import Decimal

from django.db import transaction
from django.db.models import CharField, DecimalField, F, Func, Q, QuerySet, Sum, Value
from django.db.models.functions import Coalesce
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from app_infrastructure.permissions import UserBelongsToBudgetPermission
from budgets.models import BudgetingPeriod
from categories.models.choices.category_type import CategoryType
from entities.filtersets.deposit_filterset import DepositFilterSet
from entities.models.choices.deposit_type import DepositType
from entities.models.deposit_model import Deposit
from entities.serializers.deposit_serializer import DepositSerializer
from entities.utils import (
    create_initial_categories_for_daily_expenses_deposit,
    create_initial_categories_for_other_deposit,
    create_initial_categories_for_savings_and_investments_deposit,
)
from predictions.models import ExpensePrediction


def calculate_deposit_balance() -> Func:
    """
    Function for calculate Transfers values sum for Deposit.

    Returns:
        Func: ORM function returning Sum of Deposit Transfers values.
    """
    return Coalesce(F("incomes_sum") - F("expenses_sum"), Value(0), output_field=DecimalField(decimal_places=2))


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


def get_deposit_owner_display() -> Func:
    """
    Function for generate display value of Deposit owner.

    Returns:
        Func: ORM function returning Deposit owner display value.
    """
    return Coalesce(
        F("owner__username"),
        Value("🏦 Common"),
        output_field=CharField(),
    )


class DepositViewSet(ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    permission_classes = [IsAuthenticated, UserBelongsToBudgetPermission]
    filterset_class = DepositFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = ("id", "name", "balance", "deposit_type")

    def get_queryset(self) -> QuerySet:
        """
        Retrieve Deposits for Budget passed in URL and annotate them with sum of Transfers.

        Returns:
            QuerySet: Filtered Deposit QuerySet.
        """
        return (
            self.queryset.filter(budget__pk=self.kwargs.get("budget_pk"))
            .distinct()
            .annotate(
                owner_display=get_deposit_owner_display(),
                incomes_sum=sum_deposit_transfers(CategoryType.INCOME),
                expenses_sum=sum_deposit_transfers(CategoryType.EXPENSE),
            )
            .annotate(balance=calculate_deposit_balance())
        )

    def perform_create(self, serializer: DepositSerializer) -> None:
        """
        Additionally save Budget from URL on Deposit instance during saving serializer. Create Entity object for
        Deposit representation in Transfers. Creates initial Categories for Deposit.

        Args:
            serializer [DepositSerializer]: Serializer for Deposit model.
        """
        budget_pk = self.kwargs.get("budget_pk")
        with transaction.atomic():
            deposit = serializer.save(budget_id=budget_pk, is_deposit=True)
            ExpensePrediction.objects.bulk_create(
                ExpensePrediction(
                    deposit_id=deposit.pk,
                    category=None,
                    period_id=period_id,
                    initial_plan=Decimal("0.00"),
                    current_plan=Decimal("0.00"),
                )
                for period_id in BudgetingPeriod.objects.filter(budget_id=budget_pk).values_list("id", flat=True)
            )
            if deposit.deposit_type == DepositType.DAILY_EXPENSES:
                create_initial_categories_for_daily_expenses_deposit(budget_pk=budget_pk, deposit_pk=deposit.pk)
            elif deposit.deposit_type in (DepositType.SAVINGS, DepositType.INVESTMENTS):
                create_initial_categories_for_savings_and_investments_deposit(
                    budget_pk=budget_pk, deposit_pk=deposit.pk
                )
            else:
                create_initial_categories_for_other_deposit(budget_pk=budget_pk, deposit_pk=deposit.pk)
