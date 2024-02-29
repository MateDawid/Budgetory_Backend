from typing import Any

from rest_framework import serializers
from transfers.models import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    class Meta:
        model = TransferCategory
        fields = ['id', 'name', 'description', 'category_type', 'scope', 'user', 'is_active']
        read_only_fields = ['id']

    def validate(self, attrs):
        """Validates user and name before saving serializer."""
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        user = attrs.get('user') or getattr(self.instance, 'user', None)
        scope = attrs.get('scope') or getattr(self.instance, 'scope', None)

        self._validate_user(user=user, scope=scope)
        self._validate_name(name=name, user=user, scope=scope)
        return attrs

    @staticmethod
    def _validate_user(user: Any, scope: str) -> None:
        """Check if user field is filled only when scope is "PERSONAL"."""
        if scope == TransferCategory.PERSONAL and user is None:
            raise serializers.ValidationError('User was not provided for personal transfer category.')
        if scope == TransferCategory.GLOBAL and user is not None:
            raise serializers.ValidationError('User can be provided only for personal transfer category.')

    def _validate_name(self, name: str, user: Any, scope: str) -> None:
        """Checks if user has not used transfer category name already."""
        if (
            scope == TransferCategory.PERSONAL
            and user.personal_transfer_categories.filter(name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Personal transfer category with given name already exists.')
        elif (
            scope == TransferCategory.GLOBAL
            and TransferCategory.global_transfer_categories.filter(name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Global transfer category with given name already exists.')
