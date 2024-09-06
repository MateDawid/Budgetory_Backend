from collections import OrderedDict

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError as DRFValidationError

from categories.models.transfer_category_choices import CategoryType
from categories.models.transfer_category_model import TransferCategory

ERROR_MESSAGES = {
    "Constraint “categories_transfercategory_name_unique_when_no_owner” is violated.": "Common {category_type} Category"
    " with given name already exists in Budget.",
    "Constraint “categories_transfercategory_name_unique_for_owner” is violated.": "Personal {category_type} Category"
    " with given name already exists in Budget.",
}


class TransferCategorySerializer(serializers.ModelSerializer):
    """Class for serializing TransferCategory model instances."""

    class Meta:
        model: Model = TransferCategory
        category_type: CategoryType | None = None
        fields: tuple[str] = ("id", "name", "description", "is_active", "owner", "priority")
        read_only_fields: tuple[str] = ("id",)

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Extends validation with handling database errors with more human-readable messages.

        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        budget_id = getattr(self.context.get("view"), "kwargs", {}).get("budget_pk")
        attrs["category_type"] = getattr(self.Meta, "category_type", None)
        try:
            TransferCategory(budget_id=budget_id, **attrs).full_clean()
        except DjangoValidationError as exc:
            error_message = getattr(exc, "message_dict", {}).get("__all__", ["_"])[0]
            if error_message in ERROR_MESSAGES:
                raise DRFValidationError(
                    ERROR_MESSAGES[error_message].format(category_type=attrs["category_type"].label)
                )
            raise
        return attrs
