from rest_framework.exceptions import ValidationError

from categories.models import ExpenseCategory, TransferCategory
from categories.models.transfer_category_choices import CategoryType
from transfers.models.expense_model import Expense
from transfers.serializers.transfer_serializer import TransferSerializer


class ExpenseSerializer(TransferSerializer):
    """Class for serializing Expense model instances."""

    class Meta(TransferSerializer.Meta):
        model = Expense

    def validate_category(self, category: ExpenseCategory) -> TransferCategory:
        """
        Checks if provided category.category_type is equal to CategoryType.EXPENSE.

        Args:
            category (ExpenseCategory): ExpenseCategory model instance.

        Returns:
            TransferCategory: Validated ExpenseCategory.

        Raises:
            ValidationError: Raised on invalid type of provided category.
        """
        category = super().validate_category(category)
        if category.category_type != CategoryType.EXPENSE:
            raise ValidationError("Invalid TransferCategory for Expense provided.")
        return category
