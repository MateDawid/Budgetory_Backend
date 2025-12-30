from collections import OrderedDict

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from entities.models import Deposit
from entities.models.entity_model import Entity


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity."""

    class Meta:
        model = Entity
        fields = ["id", "name", "description", "is_active", "is_deposit"]
        read_only_fields = ["id"]

    def validate_name(self, name: str):
        """
        Checks if Entity with given name exists in Budget already.

        Args:
            name: Name of Entity.

        Returns:
            str: Validated name of Entity.

        Raises:
            ValidationError: Raised if Entity with given name exists in Budget already.
        """
        if (
            self.Meta.model.objects.filter(
                budget=self.context["view"].kwargs["budget_pk"],
                name__iexact=name,
                is_deposit=self.Meta.model is Deposit,
            )
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise ValidationError(
                "{class_name} with given name already exists in Budget.".format(class_name=self.Meta.model.__name__)
            )
        return name

    def to_representation(self, instance: Entity) -> OrderedDict:
        """
        Extends model representation with "value" and "label" fields for React MUI DataGrid filtering purposes.

        Attributes:
            instance [Entity]: BudgetingPeriod model instance

        Returns:
            OrderedDict: Dictionary containing overridden values.
        """
        representation = super().to_representation(instance)
        representation["value"] = instance.id
        representation["label"] = instance.name
        return representation
