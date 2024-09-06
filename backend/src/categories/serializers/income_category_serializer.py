from categories.models.income_category_model import IncomeCategory
from categories.models.transfer_category_choices import CategoryType
from categories.serializers.transfer_category_serializer import TransferCategorySerializer


class IncomeCategorySerializer(TransferCategorySerializer):
    """Class for serializing IncomeCategory model instances."""

    class Meta(TransferCategorySerializer.Meta):
        model = IncomeCategory
        category_type = CategoryType.INCOME
