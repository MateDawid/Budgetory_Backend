from entities.models import Entity
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class EntitySerializer(serializers.ModelSerializer):
    """Serializer for Entity."""

    class Meta:
        model = Entity
        fields = ['id', 'name', 'description']
        read_only_fields = ['id']

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
        if self.Meta.model.objects.filter(budget=self.context['request'].budget, name__iexact=name).exists():
            raise ValidationError('Entity with given name already exists in Budget.')
        return name
