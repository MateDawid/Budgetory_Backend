from collections import OrderedDict

from django.contrib.auth.models import AbstractUser
from rest_framework import serializers
from transfers.managers import CategoryType
from transfers.models import TransferCategory


class TransferCategorySerializer(serializers.ModelSerializer):
    """Serializer for TransferCategory."""

    def validate(self, attrs: OrderedDict) -> OrderedDict:
        """
        Validates TransferCategory.

        Args:
            attrs [OrderedDict]: Dictionary containing given TransferCategory params

        Returns:
            OrderedDict: Dictionary with validated attrs values.
        """
        name = attrs.get('name') or getattr(self.instance, 'name')
        owner = attrs.get('owner') or getattr(self.instance, 'owner', None)
        expense_group = attrs.get('expense_group') or getattr(self.instance, 'expense_group', None)
        income_group = attrs.get('income_group') or getattr(self.instance, 'income_group', None)

        category_type = self._validate_groups(expense_group, income_group)
        if owner:
            self._validate_owner(owner)
            self._validate_personal_category_name(name, owner, category_type)
        else:
            self._validate_common_category_name(name, category_type)

        return attrs

    def _validate_owner(self, owner: AbstractUser) -> None:
        """
        Checks if provided owner belongs to Budget.

        Args:
            owner [AbstractUser]: TransferCategory owner or None.

        Raises:
            ValidationError: Raised when given User does not belong to Budget.
        """
        if not (owner == self.context['request'].budget.owner or owner in self.context['request'].budget.members.all()):
            raise serializers.ValidationError('Provided owner does not belong to Budget.')

    def _validate_personal_category_name(self, name: str, owner: AbstractUser, category_type: CategoryType) -> None:
        """
        Checks if personal TransferCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for TransferCategory
            owner [AbstractUser]: Owner of TransferCategory
            category_type [CategoryType]: Type of TransferCategory - Expense or Income

        Raises:
            ValidationError: Raised when TransferCategory for particular owner already exists in Budget.
        """
        query_filters = {
            'budget': self.context['request'].budget,
            'name__iexact': name,
        }
        query_filters = self._add_category_filters(query_filters, category_type)

        if owner.personal_categories.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError(
                f'Personal {category_type.name.title()}Category with given name already exists '
                f'in Budget for provided owner.'
            )

    def _validate_common_category_name(self, name: str, category_type: CategoryType) -> None:
        """
        Checks if common TransferCategory with provided name already exists in Budget.

        Args:
            name [str]: Name for TransferCategory
            category_type [CategoryType]: Type of TransferCategory - Expense or Income

        Raises:
            ValidationError: Raised when common TransferCategory already exists in Budget.
        """
        query_filters = {'budget': self.context['request'].budget, 'name__iexact': name, 'owner__isnull': True}
        query_filters = self._add_category_filters(query_filters, category_type)

        if TransferCategory.objects.filter(**query_filters).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError(
                f'Common {category_type.name.title()}Category with given name already exists in Budget.'
            )

    @staticmethod
    def _add_category_filters(query_filters: dict, category_type: CategoryType) -> dict:
        """
        Extends query_filters with income/expense group filters depending on CategoryType.

        Args:
            query_filters [dict]: Dictionary containing filters for TransferCategory Queryset.
            category_type [CategoryType]: Type of TransferCategory.

        Returns:
            dict: query_filters extended with TransferCategory filters.
        """
        match category_type:
            case CategoryType.EXPENSE:
                query_filters['income_group__isnull'] = True
                query_filters['expense_group__isnull'] = False
            case CategoryType.INCOME:
                query_filters['income_group__isnull'] = False
                query_filters['expense_group__isnull'] = True
        return query_filters

    @staticmethod
    def _validate_groups(expense_group, income_group) -> CategoryType:
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
        return CategoryType.INCOME if income_group else CategoryType.EXPENSE


class ExpenseCategorySerializer(TransferCategorySerializer):
    class Meta:
        model = TransferCategory
        fields = ['id', 'name', 'expense_group', 'description', 'is_active', 'owner']
        read_only_fields = ['id']

    def to_representation(self, instance: TransferCategory) -> OrderedDict:
        """
        Returns human-readable values of TransferCategory expense_group.

        Attributes:
            instance [TransferCategory]: TransferCategory model instance

        Returns:
            OrderedDict: Dictionary containing readable TransferCategory expense_group.
        """
        representation = super().to_representation(instance)
        representation['expense_group'] = instance.get_expense_group_display()

        return representation


class IncomeCategorySerializer(TransferCategorySerializer):
    class Meta:
        model = TransferCategory
        fields = ['id', 'name', 'income_group', 'description', 'is_active', 'owner']
        read_only_fields = ['id']

    def to_representation(self, instance: TransferCategory) -> OrderedDict:
        """
        Returns human-readable values of TransferCategory income_group.

        Attributes:
            instance [TransferCategory]: TransferCategory model instance

        Returns:
            OrderedDict: Dictionary containing readable TransferCategory income_group.
        """
        representation = super().to_representation(instance)
        representation['income_group'] = instance.get_income_group_display()

        return representation
