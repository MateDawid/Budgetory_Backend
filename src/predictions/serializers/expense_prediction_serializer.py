from collections import OrderedDict
from decimal import Decimal

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from budgets.models import BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from predictions.models.expense_prediction_model import ExpensePrediction


class ExpensePredictionSerializer(serializers.ModelSerializer):
    """Serializer for ExpensePrediction model."""

    class Meta:
        model: Model = ExpensePrediction
        fields = ("id", "period", "category", "current_value", "description")
        read_only_fields = ("id", "initial_value")

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
        if period.status == PeriodStatus.ACTIVE:
            raise ValidationError("New Expense Prediction cannot be added to active Budgeting Period.")
        elif period.status == PeriodStatus.CLOSED:
            raise ValidationError("New Expense Prediction cannot be added to closed Budgeting Period.")
        return period

    @staticmethod
    def validate_current_value(current_value: Decimal) -> Decimal:
        """
        Validates "current_value" field.

        Args:
            current_value [Decimal]: current_value of given ExpensePrediction.

        Returns:
            Decimal: Validated current_value of ExpensePrediction.

        Raises:
            ValidationError: Raised when "current_value" is lower than 0.01.
        """
        if current_value <= Decimal("0.00"):
            raise ValidationError("current_value: Value should be higher than 0.00.")
        return current_value

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
