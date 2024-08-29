from categories.serializers.expense_category_serializer import ExpenseCategorySerializer
from categories.views.transfer_category_viewset import TransferCategoryViewSet


class ExpenseCategoryViewSet(TransferCategoryViewSet):
    """ViewSet for managing ExpenseCategories."""

    serializer_class = ExpenseCategorySerializer
