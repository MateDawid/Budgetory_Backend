from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from budgets.models import BudgetingPeriod
from categories.models import TransferCategory
from entities.models import Deposit, Entity
from transfers.models.transfer_model import Transfer


class TransferSerializer(serializers.ModelSerializer):
    """Class for serializing Transfer model instances."""

    class Meta:
        model: Model = Transfer
        fields: tuple[str] = ("id", "name", "description", "value", "date", "period", "entity", "deposit", "category")
        read_only_fields: tuple[str] = ("id",)

    @property
    def _budget_pk(self) -> int:
        """
        Property for retrieving Budget primary key passed in URL.

        Returns:
            int: Budget model instance PK.
        """
        return int(getattr(self.context.get("view"), "kwargs", {}).get("budget_pk", 0))

    def validate_period(self, period: BudgetingPeriod) -> BudgetingPeriod:
        """
        Checks if BudgetingPeriod budget field value contains the same Budget.pk as passed in URL.

        Args:
            period (BudgetingPeriod): BudgetingPeriod model instance.

        Returns:
            BudgetingPeriod: Validated BudgetingPeriod.

        Raises:
            ValidationError: Raised on not matching budget_pk values.
        """
        if period.budget.pk != self._budget_pk:
            raise ValidationError("BudgetingPeriod from different Budget.")
        return period

    def validate_entity(self, entity: Entity) -> Entity:
        """
        Checks if Entity budget field value contains the same Budget.pk as passed in URL.

        Args:
            entity (Entity): Entity model instance.

        Returns:
            Entity: Validated Entity.

        Raises:
            ValidationError: Raised on not matching budget_pk values.
        """
        if entity.budget.pk != self._budget_pk:
            raise ValidationError("Entity from different Budget.")
        return entity

    def validate_deposit(self, deposit: Deposit) -> Deposit:
        """
        Checks if Deposit budget field value contains the same Budget.pk as passed in URL.

        Args:
            deposit (Deposit): Deposit model instance.

        Returns:
            Deposit: Validated Deposit.

        Raises:
            ValidationError: Raised on not matching budget_pk values.
        """
        if deposit.budget.pk != self._budget_pk:
            raise ValidationError("Deposit from different Budget.")
        return deposit

    def validate_category(self, category: TransferCategory) -> TransferCategory:
        """
        Checks if TransferCategory budget field value contains the same Budget.pk as passed in URL.

        Args:
            category (TransferCategory): TransferCategory model instance.

        Returns:
            TransferCategory: Validated TransferCategory.

        Raises:
            ValidationError: Raised on not matching budget_pk values.
        """
        if category.budget.pk != self._budget_pk:
            raise ValidationError("TransferCategory from different Budget.")
        return category
