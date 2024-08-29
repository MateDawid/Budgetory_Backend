from collections import OrderedDict

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from categories.models import TransferCategory
from categories.models.income_category_model import IncomeCategory

ERROR_MESSAGES = {
    "Constraint “categories_transfercategory_name_unique_when_no_owner” is violated.": "Common category with given "
    "name already exists in Budget.",
    "Constraint “categories_transfercategory_name_unique_for_owner” is violated.": "Personal category with given name "
    "already exists in Budget.",
}


class TransferCategorySerializer(serializers.ModelSerializer):
    """Class for serializing TransferCategory model instances."""

    class Meta:
        model = TransferCategory
        fields = ["id", "name", "description", "is_active", "owner", "priority"]
        read_only_fields = ["id"]

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Extends validation with handling database errors with more human-readable messages.

        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        budget_id = getattr(self.context.get("view"), "kwargs", {}).get("budget_pk")
        try:
            IncomeCategory(budget_id=budget_id, **attrs).full_clean()
        except DjangoValidationError as exc:
            error_message = getattr(exc, "message_dict", {}).get("__all__", ["_"])[0]
            if error_message in ERROR_MESSAGES:
                raise DRFValidationError(ERROR_MESSAGES[error_message])
            raise
        return attrs
