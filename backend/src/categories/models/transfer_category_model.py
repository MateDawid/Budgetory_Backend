from categories.managers.expense_category_manager import ExpenseCategoryManager
from categories.managers.income_category_manager import IncomeCategoryManager
from categories.models.category_priority_choices import CategoryPriority
from categories.models.category_type_choices import CategoryType
from django.conf import settings
from django.db import models
from django.db.models import CheckConstraint, Q, UniqueConstraint


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

    objects = models.Manager()
    income_categories = IncomeCategoryManager()
    expense_categories = ExpenseCategoryManager()

    class Meta:
        verbose_name_plural = "transfer categories"
        constraints = (
            CheckConstraint(
                name="%(app_label)s_%(class)s_correct_priority_for_type",
                check=(
                    Q(category_type=CategoryType.INCOME, priority=CategoryPriority.INCOMES)
                    | (Q(category_type=CategoryType.EXPENSE) & ~Q(priority=CategoryPriority.INCOMES))
                ),
            ),
            UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique_for_owner",
                fields=("budget", "category_type", "name", "owner"),
                condition=Q(owner__isnull=False),
            ),
            UniqueConstraint(
                name="%(app_label)s_%(class)s_name_unique_when_no_owner",
                fields=("budget", "category_type", "name"),
                condition=Q(owner__isnull=True),
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
