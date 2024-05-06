from collections import OrderedDict

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from transfers.models import TransferCategory


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
        owner = attrs.get('owner') or getattr(self.instance, 'owner', None)

        self._validate_owner(owner)
        self._validate_name(name, owner)

        return attrs

    def _validate_owner(self, owner: AbstractUser | None):
        if owner and not (
            owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()
        ):
            raise serializers.ValidationError('Provided owner does not belong to Budget.')

    def _validate_name(self, name: str | None, owner: AbstractUser):
        if (
            owner
            and owner.personal_categories.filter(group__budget=self.context['request'].budget, name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError(
                'Personal TransferCategory with given name already exists in Budget for provided owner.'
            )
        elif (
            owner is None
            and TransferCategory.objects.filter(
                group__budget=self.context['request'].budget, owner__isnull=True, name__iexact=name
            )
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Common TransferCategory with given name already exists in Budget.')
