from deposits.models import Deposit
from django.contrib.auth.models import AbstractUser
from entities.models import Entity
from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class DepositSerializer(serializers.ModelSerializer):
    """Serializer for Deposit."""

    is_active = serializers.BooleanField(default=True)

    class Meta:
        model = Deposit
        fields = ['id', 'name', 'description', 'deposit_type', 'is_active', 'owner']
        read_only_fields = ['id']

    def validate_name(self, name: str):
        """
        Checks if Deposit with given name exists in Budget already.

        Args:
            name: Name of Deposit.

        Returns:
            str: Validated name of Deposit.

        Raises:
            ValidationError: Raised if Deposit with given name exists in Budget already.
        """
        if self.Meta.model.objects.filter(budget=self.context['request'].budget, name__iexact=name).exists():
            raise ValidationError('Deposit with given name already exists in Budget.')
        elif Entity.objects.filter(budget=self.context['request'].budget, name__iexact=name).exists():
            raise ValidationError('Entity with given name already exists in Budget.')
        return name

    def validate_owner(self, owner: AbstractUser | None):
        """
        Checks if provided Deposit owner is part of Budget.

        Args:
            owner [AbstractUser | None]:

        Returns:
            AbstractUser | None: User model instance or None.
        """
        if owner and not (
            owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()
        ):
            raise ValidationError('Provided owner does not belong to Budget.')
        return owner

    def to_representation(self, instance: Deposit):
        """
        Returns human readable value of Deposit deposit_type.

        Attributes:
            deposit [Deposit]: Deposit model instance

        Returns:
            str: Readable Deposit deposit_type
        """
        representation = super().to_representation(instance)
        representation['deposit_type'] = instance.get_deposit_type_display()

        return representation
