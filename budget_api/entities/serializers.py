from typing import Any

from entities.models import Entity
from rest_framework import serializers


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity."""

    class Meta:
        model = Entity
        fields = ['id', 'name', 'description', 'type', 'user']
        read_only_fields = ['id']

    def validate(self, attrs):
        """Validates user and name before saving serializer."""
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        user = attrs.get('user') or getattr(self.instance, 'user', None)
        type_ = attrs.get('type') or getattr(self.instance, 'type', None)

        self._validate_user(user=user, type_=type_)
        self._validate_name(name=name, user=user, type_=type_)
        return attrs

    @staticmethod
    def _validate_user(user: Any, type_: str) -> None:
        """Check if user field is filled only when type is "PERSONAL"."""
        if type_ == 'PERSONAL' and user is None:
            raise serializers.ValidationError('User was not provided for personal Entity.')
        if type_ == 'GLOBAL' and user is not None:
            raise serializers.ValidationError('User can be provided only for personal Entities.')

    def _validate_name(self, name: str, user: Any, type_: str) -> None:
        """Checks if user has not used deposit name already."""
        if (
            type_ == 'PERSONAL'
            and user.personal_entities.filter(name__iexact=name).exclude(id=getattr(self.instance, 'id', None)).exists()
        ):
            raise serializers.ValidationError('Personal entity with given name already exists.')
        elif (
            type_ == 'GLOBAL'
            and Entity.global_entities.filter(name__iexact=name).exclude(id=getattr(self.instance, 'id', None)).exists()
        ):
            raise serializers.ValidationError('Global entity with given name already exists.')
