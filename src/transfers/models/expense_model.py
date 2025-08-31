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
        if not self.category.category_type == CategoryType.EXPENSE:
            raise ValidationError("Expense model instance can not be created with IncomeCategory.")
        if not getattr(self.entity, "is_deposit", False):
            super().save(*args, **kwargs)
            return
        # Handling Transfer between deposits
        with transaction.atomic():
            try:
                deposit_income = Income.objects.create(
                    name=self.name,
                    description=self.description,
                    value=None,
                    date=self.date,
                    period=self.period,
                    entity=self.deposit,
                    deposit=self.entity,
                    category=TransferCategory.objects.get(
                        budget=self.period.budget,
                        category_type=CategoryType.INCOME,
                        priority=CategoryPriority.DEPOSIT_INCOME,
                    ),
                )
                setattr(self, "deposit_income", deposit_income)
                super().save(*args, **kwargs)
            except Exception as e:
                logger.error(f"Creating Deposit Transfers failed. | Reason: {str(e)}")
