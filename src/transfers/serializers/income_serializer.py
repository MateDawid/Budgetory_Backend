from rest_framework.exceptions import ValidationError

from categories.models import IncomeCategory, TransferCategory
from categories.models.transfer_category_choices import CategoryType
from transfers.models.income_model import Income
from transfers.serializers.transfer_serializer import TransferSerializer


class IncomeSerializer(TransferSerializer):
    """Class for serializing IncomeCategory model instances."""

    class Meta(TransferSerializer.Meta):
        model = Income

    def validate_category(self, category: IncomeCategory) -> TransferCategory:
        """
        Checks if provided category.category_type is equal to CategoryType.INCOME.

        Args:
            category (IncomeCategory): IncomeCategory model instance.

        Returns:
            TransferCategory: Validated IncomeCategory.

        Raises:
            ValidationError: Raised on invalid type of provided category.
        """
        category = super().validate_category(category)
        if category.category_type != CategoryType.INCOME:
            raise ValidationError("Invalid TransferCategory for Income provided.")
        return category
