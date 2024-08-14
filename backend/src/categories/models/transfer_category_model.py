from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q


class CategoryType(models.IntegerChoices):
    """Choices for TransferCategory type value."""

    INCOME = 0, "Income"
    EXPENSE = 1, "Expense"


class CategoryPriority(models.IntegerChoices):
    """
    Choices for TransferCategory priority value.

    Value 0 (INCOMES) dedicated for CategoryType.INCOME.
    Values 1-4 dedicated for CategoryType.EXPENSE.
    """

    INCOMES = 0, "Incomes"
    MOST_IMPORTANT = 1, "Most important"
    DEBTS = 2, "Debts"
    SAVINGS = 3, "Savings"
    OTHERS = 4, "Others"


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE, related_name="transfer_categories")
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="personal_transfer_categories",
    )
    is_active = models.BooleanField(default=True)
    category_type = models.PositiveSmallIntegerField(choices=CategoryType.choices, null=False, blank=False)
    priority = models.PositiveSmallIntegerField(choices=CategoryPriority.choices, null=False, blank=False)

    class Meta:
        verbose_name_plural = "transfer categories"
        constraints = (
            CheckConstraint(
                name="%(app_label)s_%(class)s_correct_priority_for_type",
                check=(
                    models.Q(category_type=CategoryType.INCOME, priority=CategoryPriority.INCOMES)
                    | (models.Q(category_type=CategoryType.EXPENSE) & ~Q(priority=CategoryPriority.INCOMES))
                ),
            ),
        )

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        return f"({self.category_type}) {self.name}"
