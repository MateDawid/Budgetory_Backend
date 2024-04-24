from collections import OrderedDict

from rest_framework import serializers
from transfers.models.transfer_category_model import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    class Meta:
        model = TransferCategory
        fields = ['id', 'group', 'name', 'description', 'owner', 'is_active']
        read_only_fields = ['id']

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Checks if common or personal TransferCategory already exists in Budget.

        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        user = attrs.get('user') or getattr(self.instance, 'user', None)

        if (
            user
            and user.personal_categories.filter(name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Personal TransferCategory with given name already exists in Budget.')
        elif (
            user is None
            and TransferCategory.objects.filter(owner__isnull=True, name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Common TransferCategory with given name already exists in Budget.')

        return attrs

    # TODO - validate if group from accessible budget
    # TODO - validate if user from accessible budget
