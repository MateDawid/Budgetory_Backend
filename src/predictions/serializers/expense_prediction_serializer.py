from collections import OrderedDict
from decimal import Decimal

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from budgets.models import BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from predictions.models.expense_prediction_model import ExpensePrediction


class ExpensePredictionSerializer(serializers.ModelSerializer):
    """Serializer for ExpensePrediction model."""

    current_result = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_funds_left = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    current_progress = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_plan = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_result = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)
    previous_funds_left = serializers.DecimalField(max_digits=20, decimal_places=2, default=0, read_only=True)

    class Meta:
        model: Model = ExpensePrediction
        fields = (
            "id",
            "period",
            "category",
            "description",
            "initial_plan",
            "current_plan",
            "current_result",
            "current_funds_left",
            "current_progress",
            "previous_plan",
            "previous_result",
            "previous_funds_left",
        )
        read_only_fields = (
            "id",
            "initial_plan",
            "current_result",
            "previous_result",
            "previous_plan",
            "current_funds_left",
            "previous_funds_left",
            "current_progress",
        )

    @staticmethod
    def validate_category(category: TransferCategory) -> TransferCategory:
        """
        Validates "category" field.

        Args:
            category [TransferCategory]: TransferCategory of given ExpensePrediction.

        Returns:
            TransferCategory: Validated category of ExpensePrediction.

        Raises:
            ValidationError: Raised when TransferCategory.category_type is not EXPENSE.
        """
        if category.category_type != CategoryType.EXPENSE:
            raise ValidationError("Incorrect category provided. Please provide expense category.")
        return category

    def validate_period(self, period: BudgetingPeriod) -> BudgetingPeriod:
        """
        Validates "period" field.

        Args:
            period [BudgetingPeriod]: BudgetingPeriod of given ExpensePrediction.

        Returns:
            BudgetingPeriod: Validated category of ExpensePrediction.

        Raises:
            ValidationError: Raised when:
                * User tries to change BudgetingPeriod of existing ExpensePrediction
                * User tries to create ExpensePrediction in ACTIVE or CLOSED BudgetingPeriod
        """
        if self.instance and self.instance.period != period:
            raise ValidationError("Budgeting Period for Expense Prediction cannot be changed.")
        if not self.instance and period.status == PeriodStatus.ACTIVE:
            raise ValidationError("New Expense Prediction cannot be added to active Budgeting Period.")
        elif not self.instance and period.status == PeriodStatus.CLOSED:
            raise ValidationError("New Expense Prediction cannot be added to closed Budgeting Period.")
        return period

    @staticmethod
    def validate_current_plan(current_plan: Decimal) -> Decimal:
        """
        Validates "current_plan" field.

        Args:
            current_plan [Decimal]: current_plan of given ExpensePrediction.

        Returns:
            Decimal: Validated current_plan of ExpensePrediction.

        Raises:
            ValidationError: Raised when "current_plan" is lower than 0.01.
        """
        if current_plan <= Decimal("0.00"):
            raise ValidationError("Value should be higher than 0.00.")
        return current_plan

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates if BudgetingPeriod of ExpensePrediction status is CLOSED, to stop further validations.

        Args:
            attrs (OrderedDict): Provided ExpensePrediction values.

        Returns:
            OrderedDict: Validated ExpensePrediction values.

        Raises:
            ValidationError: Raised when ExpensePrediction's period status is CLOSED.
        """
        if self.instance and self.instance.period.status == PeriodStatus.CLOSED:
            raise ValidationError("Expense Prediction cannot be changed when Budgeting Period is closed.")
        return attrs

    def to_representation(self, instance: ExpensePrediction) -> OrderedDict:
        """
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [BudgetingPeriod]: BudgetingPeriod model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["category_display"] = f"📉{instance.category.name}"
        representation["category_deposit"] = getattr(instance.category.deposit, "name", None)
        representation["category_priority"] = CategoryPriority(instance.category.priority).label
        return representation
