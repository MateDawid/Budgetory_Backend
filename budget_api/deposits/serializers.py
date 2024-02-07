from deposits.models import Deposit
from rest_framework import serializers


class DepositSerializer(serializers.ModelSerializer):
    """Serializer for Deposit."""

    class Meta:
        model = Deposit
        fields = ['id', 'name', 'description', 'is_active']
        read_only_fields = ['id']

    def validate_name(self, value: str) -> str:
        """Checks if user has not used deposit name already."""
        try:
            self.Meta.model.objects.get(user=self.context['request'].user, name=value)
        except self.Meta.model.DoesNotExist:
            pass
        else:
            raise serializers.ValidationError(f'Users deposit with name {value} already exists.')
        return value
