from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from transfers.models.transfer_category_group_model import TransferCategoryGroup


class TransferCategoryGroupSerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    class Meta:
        model = TransferCategoryGroup
        fields = ['id', 'name', 'description', 'transfer_type']
        read_only_fields = ['id']

    def validate_name(self, name: str):
        """
        Checks if TransferCategoryGroup with given name exists in Budget already.

        Args:
            name: Name of TransferCategoryGroup.

        Returns:
            str: Validated name of TransferCategoryGroup.

        Raises:
            ValidationError: Raised if TransferCategoryGroup with given name exists in Budget already.
        """
        if self.Meta.model.objects.filter(budget=self.context['request'].budget, name__iexact=name).exists():
            raise ValidationError('TransferCategoryGroup with given name already exists in Budget.')
        return name

    def to_representation(self, instance: TransferCategoryGroup):
        """
        Returns human-readable value of TransferCategoryGroup transfer_type.

        Attributes:
            deposit [TransferCategoryGroup]: TransferCategoryGroup model instance

        Returns:
            str: Readable TransferCategoryGroup transfer_type
        """
        representation = super().to_representation(instance)
        representation['transfer_type'] = instance.get_transfer_type_display()

        return representation
