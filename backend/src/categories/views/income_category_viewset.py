from categories.serializers.income_category_serializer import IncomeCategorySerializer
from categories.views.transfer_category_viewset import TransferCategoryViewSet


class IncomeCategoryViewSet(TransferCategoryViewSet):
    """ViewSet for managing IncomeCategories."""

    serializer_class = IncomeCategorySerializer
