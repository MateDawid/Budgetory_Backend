from categories.models.expense_category_model import ExpenseCategory
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


class ExpenseCategorySerializer(TransferCategorySerializer):
    """Class for serializing ExpenseCategory model instances."""

    class Meta(TransferCategorySerializer.Meta):
        model = ExpenseCategory
