from categories.models.income_category_model import IncomeCategory
from categories.serializers.transfer_category_serializer import (
    TransferCategorySerializer,
)


class IncomeCategorySerializer(TransferCategorySerializer):
    """Class for serializing IncomeCategory model instances."""

    class Meta(TransferCategorySerializer.Meta):
        model = IncomeCategory
