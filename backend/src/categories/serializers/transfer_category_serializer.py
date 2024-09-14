from collections import OrderedDict

from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from categories.models.transfer_category_model import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Class for serializing TransferCategory model instances."""

    class Meta:
        model: Model = TransferCategory
        fields: tuple[str] = ("id", "name", "description", "is_active", "owner", "priority")
        read_only_fields: tuple[str] = ("id",)

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates input parameters.

        Args:
            attrs [OrderedDict]: Input parameters.

        Returns:
            attrs: Validated parameters.
        """
        payload = {
            "budget_id": getattr(self.context.get("view"), "kwargs", {}).get("budget_pk"),
            "name": attrs.get("name") or getattr(self.instance, "name", None),
        }
        if owner_id := (attrs.get("owner") or getattr(self.instance, "owner", None)):
            payload["owner"] = owner_id
        if self.Meta.model.objects.filter(**payload).exclude(id=getattr(self.instance, "id", None)).exists():
            raise ValidationError(
                f"{'Personal' if owner_id else 'Common'} {self.Meta.model.__name__} with given "
                f"name already exists in Budget."
            )
        return attrs
