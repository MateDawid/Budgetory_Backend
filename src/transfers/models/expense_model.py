import logging

from django.core.exceptions import ValidationError
from django.db import transaction

from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.managers.expense_manager import ExpenseManager
from transfers.models.income_model import Income
from transfers.models.transfer_model import Transfer

logger = logging.getLogger("default")


class Expense(Transfer):
    """Expense proxy model for Transfer with ExpenseCategory as category."""

    objects = ExpenseManager()

    class Meta:
        proxy = True
        verbose_name_plural = "expenses"

    def save(self, *args, **kwargs) -> None:
        """
        Save method overridden to validate category_type of Expense.category
        and handle creating Transfer between Deposits.
        """
        if not self.category.category_type == CategoryType.EXPENSE:
            raise ValidationError("Expense model instance can not be created with IncomeCategory.")
        if not getattr(self.entity, "is_deposit", False):
            super().save(*args, **kwargs)
            return
        if self.entity == self.deposit:
            # Triggering IntegrityError raised by database constraint.
            super().save(*args, **kwargs)
            return
        # Handling Transfer between deposits
        with transaction.atomic():
            try:
                deposit_income_payload = {
                    "name": self.name,
                    "description": self.description,
                    "value": self.value,
                    "date": self.date,
                    "period": self.period,
                    "entity": self.deposit,
                    "deposit": self.entity,
                    "category": TransferCategory.objects.get(
                        budget=self.period.budget,
                        category_type=CategoryType.INCOME,
                        priority=CategoryPriority.DEPOSIT_INCOME,
                    ),
                }
                if self._state.adding:
                    deposit_income = Income.objects.create(**deposit_income_payload)
                    setattr(self, "deposit_income", deposit_income)
                else:
                    Income.objects.filter(id=self.deposit_income.id).update(**deposit_income_payload)
                super().save(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{'Creating' if self._state.adding else 'Updating'} Deposit Transfers failed. "
                    f"{f'Expense id: {self.id}' if self.id else ''} | Reason: {str(e)}"
                )
                raise e

    def delete(self, using=None, keep_parents=False) -> None:
        """
        Delete method overridden handle deleting Transfer between Deposits.
        """
        with transaction.atomic():
            try:
                super().delete(using, keep_parents)
                Income.objects.filter(id=getattr(self.deposit_income, "id", None)).delete()
            except Exception as e:
                logger.error(f"Deleting Deposit Transfers failed. | Reason: {str(e)}")
                raise e
