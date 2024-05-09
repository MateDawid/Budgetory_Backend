from collections import OrderedDict

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from transfers.models import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    class Meta:
        model = TransferCategory
        fields = ['id', 'name', 'expense_group', 'income_group', 'description', 'is_active', 'owner']
        read_only_fields = ['id']

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates TransferCategory.

        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        owner = attrs.get('owner') or getattr(self.instance, 'owner', None)
        expense_group = attrs.get('expense_group') or getattr(self.instance, 'expense_group', None)
        income_group = attrs.get('income_group') or getattr(self.instance, 'income_group', None)

        self._validate_owner(owner)
        self._validate_name(name, owner)
        self._validate_groups(expense_group, income_group)

        return attrs

    def _validate_owner(self, owner: AbstractUser | None) -> None:
        """
        Checks if provided owner belongs to Budget.

        Args:
            owner [AbstractUser | None]:  TransferCategory owner or None.

        Raises:
            ValidationError: Raised when given User does not belong to Budget.
        """
        if owner and not (
            owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()
        ):
            raise serializers.ValidationError('Provided owner does not belong to Budget.')

    def _validate_name(self, name: str | None, owner: AbstractUser | None) -> None:
        """
        Checks if personal (when owner provided) or common TransferCategory with provided name
        already exists in Budget.

        Args:
            name [str]: Name for TransferCategory
            owner [AbstractUser | None]: Owner of TransferCategory or None

        Raises:
            ValidationError: Raised when TransferCategory for particular owner (including None value) already
            exists in Budget.
        """
        if (
            owner
            and owner.personal_categories.filter(budget=self.context['request'].budget, name__iexact=name)
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError(
                'Personal TransferCategory with given name already exists in Budget for provided owner.'
            )
        elif (
            owner is None
            and TransferCategory.objects.filter(
                budget=self.context['request'].budget, owner__isnull=True, name__iexact=name
            )
            .exclude(id=getattr(self.instance, 'id', None))
            .exists()
        ):
            raise serializers.ValidationError('Common TransferCategory with given name already exists in Budget.')

    @staticmethod
    def _validate_groups(expense_group, income_group) -> None:
        """
        Checks if exactly one of groups was indicated for TransferCategory.

        Args:
            expense_group [int | None]: Expense group number or None
            income_group [int | None]: Income group number or None

        Raises:
            ValidationError: Raised when no group was selected or when both groups were selected.
        """
        if expense_group and income_group:
            raise serializers.ValidationError('Only one type of group can be selected for TransferCategory.')
        elif not (expense_group or income_group):
            raise serializers.ValidationError('Expense group or income group has to be selected for TransferCategory.')

    def to_representation(self, instance: TransferCategory) -> OrderedDict:
        """
        Returns human-readable values of TransferCategory expense_group and income_group.

        Attributes:
            instance [TransferCategory]: TransferCategory model instance

        Returns:
            OrderedDict: Dictionary containing readable TransferCategory expense_group and income_group.
        """
        representation = super().to_representation(instance)
        representation['income_group'] = instance.get_income_group_display()
        representation['expense_group'] = instance.get_expense_group_display()

        return representation
