from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType


class TransferCategory(models.Model):
    """TransferCategory model for grouping Transfer model instances."""

    budget = models.ForeignKey("budgets.Budget", on_delete=models.CASCADE, related_name="transfer_categories")
    name = models.CharField(max_length=128)
    description = models.CharField(max_length=255, blank=True, null=True)
    deposit = models.ForeignKey(
        "entities.Deposit", on_delete=models.CASCADE, related_name="transfer_categories", blank=False, null=False
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
                    Q(category_type=CategoryType.INCOME, priority__in=CategoryPriority.income_priorities())
                    | Q(category_type=CategoryType.EXPENSE, priority__in=CategoryPriority.expense_priorities())
                ),
            ),
            UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique_for_deposit",
                fields=("budget", "category_type", "name", "deposit"),
                condition=Q(deposit__isnull=False),
            ),
        )

    def __str__(self) -> str:
        """
        Returns string representation of TransferCategory model instance.

        Returns:
            str: Custom string representation of instance.
        """
        label = ""
        for category_type in CategoryType:
            if category_type.value == self.category_type:
                label = category_type.label
                break
        return f"({label}) {self.name}"
