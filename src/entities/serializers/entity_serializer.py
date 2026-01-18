from rest_flex_fields import FlexFieldsModelSerializer
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, IntegerField

from entities.models import Deposit
from entities.models.entity_model import Entity


class EntitySerializer(FlexFieldsModelSerializer):
    """Serializer for Entity."""

    value = IntegerField(source="id", read_only=True, help_text="Field for React MUI select fields choice value.")
    label = CharField(source="name", read_only=True, help_text="Field for React MUI select fields choice label.")

    class Meta:
        model = Entity
        fields = ["id", "name", "description", "is_active", "is_deposit", "value", "label"]
        read_only_fields = ["id", "value", "label"]

    def validate_name(self, name: str):
        """
        Checks if Entity with given name exists in Wallet already.

        Args:
            name: Name of Entity.

        Returns:
            str: Validated name of Entity.

        Raises:
            ValidationError: Raised if Entity with given name exists in Wallet already.
        """
        if (
            self.Meta.model.objects.filter(
                wallet=self.context["view"].kwargs["wallet_pk"],
                name__iexact=name,
                is_deposit=self.Meta.model is Deposit,
            )
            .exclude(pk=getattr(self.instance, "pk", None))
            .exists()
        ):
            raise ValidationError(
                "{class_name} with given name already exists in Wallet.".format(class_name=self.Meta.model.__name__)
            )
        return name
