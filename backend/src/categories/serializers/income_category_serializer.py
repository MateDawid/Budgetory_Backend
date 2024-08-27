from collections import OrderedDict

from django.db.models import Model
from rest_framework import serializers

from app_users.models import User
from categories.models import TransferCategory
from categories.models.expense_category_model import ExpenseCategory
from categories.models.income_category_model import IncomeCategory

CATEGORY_NAME_ERRORS = {
    "PERSONAL": "Personal {class_name} with given name already exists in Budget for provided owner.",
    "COMMON": "Common {class_name} with given name already exists in Budget.",
}


class TransferCategorySerializer(serializers.ModelSerializer):
    """Base class for TransferCategorySerializers"""

    class Meta:
        model = TransferCategory
        fields = ["id", "name", "description", "is_active", "owner", "priority"]
        read_only_fields = ["id"]

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates TransferCategory.
        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params
        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """

        x = TransferCategory(**attrs).full_clean()

        return attrs
