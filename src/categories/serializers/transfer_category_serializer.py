from collections import OrderedDict

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from categories.models.transfer_category_model import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Class for serializing TransferCategory model instances."""

    class Meta:
        model: Model = TransferCategory
        fields: tuple[str] = ("id", "category_type", "priority", "name", "description", "is_active", "owner")
        read_only_fields: tuple[str] = ("id",)

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates input parameters.

        Args:
            attrs [OrderedDict]: Input parameters.

        Returns:
            OrderedDict: Validated parameters.
        """
        self._validate_type_and_priority(category_type=attrs.get("category_type"), priority=attrs.get("priority"))
        self._validate_category_uniqueness(attrs)
        return attrs

    @staticmethod
    def _validate_type_and_priority(category_type: CategoryType, priority: CategoryPriority) -> None:
        """
        Checks if proper CategoryPriority was selected for specified category_type field value.

        Args:
            category_type (CategoryType): Selected CategoryType value.
            priority (CategoryPriority): Selected CategoryPriority value.

        Raises:
            ValidationError: Raised when invalid CategoryPriority selected for category_type field value.
        """
        if (
            category_type == CategoryType.EXPENSE
            and priority in CategoryPriority.income_priorities()
            or category_type == CategoryType.INCOME
            and priority in CategoryPriority.expense_priorities()
        ):
            raise ValidationError("Invalid priority selected for specified Category type.")

    def _validate_category_uniqueness(self, attrs: OrderedDict) -> None:
        """
        Checks if TransferCategory name is unique in for specified owner value.

        Args:
            attrs (OrderedDict): Input parameters.

        Raises:
            ValidationError: Raised when TransferCategory name already used for specified owner in given Budget.
        """
        payload = {
            "budget_id": getattr(self.context.get("view"), "kwargs", {}).get("budget_pk"),
            "name": attrs.get("name") or getattr(self.instance, "name", None),
        }
        if owner_id := (attrs.get("owner") or getattr(self.instance, "owner", None)):
            payload["owner"] = owner_id
        if self.Meta.model.objects.filter(**payload).exclude(id=getattr(self.instance, "id", None)).exists():
            raise ValidationError(
                f"{'Personal' if owner_id else 'Common'} Category with given " f"name already exists in Budget."
            )

    def to_representation(self, instance: TransferCategory) -> OrderedDict:
        """
        Overrides "owner" field representation for None value for Frontend proper display.
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [TransferCategory]: TransferCategory model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["owner"] = getattr(instance.owner, "id", -1)
        representation["value"] = instance.id
        representation["label"] = f"📉 {instance.name}"
        return representation
