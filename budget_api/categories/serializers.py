from collections import OrderedDict

from categories.models import ExpenseCategory, IncomeCategory
from django.contrib.auth.models import AbstractUser
from rest_framework import serializers


class IncomeCategorySerializer(serializers.ModelSerializer):
    """Serializer for IncomeCategory model."""

    class Meta:
        model = IncomeCategory
        fields = ['id', 'name', 'group', 'description', 'is_active', 'owner']
        read_only_fields = ['id']

    def to_representation(self, instance: IncomeCategory) -> OrderedDict:
        """
        Returns human-readable values of IncomeCategory group.

        Attributes:
            instance [IncomeCategory]: IncomeCategory model instance

        Returns:
            OrderedDict: Dictionary containing readable IncomeCategory expense_group.
        """
        representation = super().to_representation(instance)
        representation['group'] = instance.get_group_display()

        return representation

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates IncomeCategory.

        Args:
            attrs [OrderedDict]: Dictionary containing given IncomeCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        name = attrs.get('name') or getattr(self.instance, 'name')
        owner = attrs.get('owner') or getattr(self.instance, 'owner', None)

        if owner:
            self._validate_owner(owner)
            self._validate_personal_category_name(name, owner)
        else:
            self._validate_common_category_name(name)

        return attrs

    def _validate_owner(self, owner: AbstractUser) -> None:
        """
        Checks if provided owner belongs to Budget.

        Args:
            owner [AbstractUser]: IncomeCategory owner or None.

        Raises:
            ValidationError: Raised when given User does not belong to Budget.
        """
        if not (owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()):
            raise serializers.ValidationError('Provided owner does not belong to Budget.')

    def _validate_personal_category_name(self, name: str, owner: AbstractUser) -> None:
        """
        Checks if personal IncomeCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for IncomeCategory
            owner [AbstractUser]: Owner of IncomeCategory

        Raises:
            ValidationError: Raised when IncomeCategory for particular owner already exists in Budget.
        """
        query_filters = {
            'budget': self.context['request'].budget,
            'name__iexact': name,
        }
        if owner.income_categories.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError(
                'Personal IncomeCategory with given name already exists in Budget for provided owner.'
            )

    def _validate_common_category_name(self, name: str) -> None:
        """
        Checks if common IncomeCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for IncomeCategory

        Raises:
            ValidationError: Raised when common IncomeCategory already exists in Budget.
        """
        query_filters = {'budget': self.context['request'].budget, 'name__iexact': name, 'owner__isnull': True}

        if IncomeCategory.objects.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError('Common IncomeCategory with given name already exists in Budget.')


class ExpenseCategorySerializer(serializers.ModelSerializer):
    """Serializer for ExpenseCategory model."""

    class Meta:
        model = ExpenseCategory
        fields = ['id', 'name', 'group', 'description', 'is_active', 'owner']
        read_only_fields = ['id']

    def to_representation(self, instance: ExpenseCategory) -> OrderedDict:
        """
        Returns human-readable values of ExpenseCategory group.

        Attributes:
            instance [ExpenseCategory]: ExpenseCategory model instance

        Returns:
            OrderedDict: Dictionary containing readable ExpenseCategory expense_group.
        """
        representation = super().to_representation(instance)
        representation['group'] = instance.get_group_display()

        return representation

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates ExpenseCategory.

        Args:
            attrs [OrderedDict]: Dictionary containing given ExpenseCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        name = attrs.get('name') or getattr(self.instance, 'name')
        owner = attrs.get('owner') or getattr(self.instance, 'owner', None)

        if owner:
            self._validate_owner(owner)
            self._validate_personal_category_name(name, owner)
        else:
            self._validate_common_category_name(name)

        return attrs

    def _validate_owner(self, owner: AbstractUser) -> None:
        """
        Checks if provided owner belongs to Budget.

        Args:
            owner [AbstractUser]: ExpenseCategory owner or None.

        Raises:
            ValidationError: Raised when given User does not belong to Budget.
        """
        if not (owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()):
            raise serializers.ValidationError('Provided owner does not belong to Budget.')

    def _validate_personal_category_name(self, name: str, owner: AbstractUser) -> None:
        """
        Checks if personal ExpenseCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for ExpenseCategory
            owner [AbstractUser]: Owner of ExpenseCategory

        Raises:
            ValidationError: Raised when ExpenseCategory for particular owner already exists in Budget.
        """
        query_filters = {'budget': self.context['request'].budget, 'name__iexact': name, 'owner': owner}
        if ExpenseCategory.objects.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError(
                'Personal ExpenseCategory with given name already exists in Budget for provided owner.'
            )

    def _validate_common_category_name(self, name: str) -> None:
        """
        Checks if common ExpenseCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for ExpenseCategory

        Raises:
            ValidationError: Raised when common ExpenseCategory already exists in Budget.
        """
        query_filters = {'budget': self.context['request'].budget, 'name__iexact': name, 'owner__isnull': True}

        if ExpenseCategory.objects.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError('Common ExpenseCategory with given name already exists in Budget.')
