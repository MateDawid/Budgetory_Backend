from enum import Enum, auto

from django.db.models import Case, Manager, Q, QuerySet, Value, When


class CategoryType(Enum):
    """
    Types of TransferCategory model instances.
    """

    EXPENSE = auto()
    INCOME = auto()
    OPERATIONAL = auto()


class TransferCategoryQuerySet(QuerySet):
    """Custom QuerySet for handling many types of TransferCategories."""

    def expense_categories(self) -> QuerySet:
        """
        Returns QuerySet filtered with EXPENSE TransferCategory type.

        Returns:
            QuerySet: Filtered QuerySet containing only EXPENSE TransferCategory type.
        """
        return self.filter(category_type=CategoryType.EXPENSE.value)

    def income_categories(self) -> QuerySet:
        """
        Returns QuerySet filtered with INCOME TransferCategory type.

        Returns:
            QuerySet: Filtered QuerySet containing only INCOME TransferCategory type.
        """
        return self.filter(category_type=CategoryType.INCOME.value)

    def operational_categories(self) -> QuerySet:
        """
        Returns QuerySet filtered with OPERATIONAL TransferCategory type.

        Returns:
            QuerySet: Filtered QuerySet containing only OPERATIONAL TransferCategory type.
        """
        return self.filter(category_type=CategoryType.OPERATIONAL.value)


class TransferCategoryManager(Manager):
    def get_queryset(self) -> QuerySet:
        """
        Extends TransferCategoryQuerySet with additional category_type field.

        Returns:
            QuerySet: QuerySet for TransferCategory model extended with category_type field.

        """
        return TransferCategoryQuerySet(self.model, using=self._db).annotate(
            category_type=Case(
                When(Q(income_group__isnull=False, expense_group__isnull=True), then=Value(CategoryType.INCOME.value)),
                When(Q(income_group__isnull=True, expense_group__isnull=False), then=Value(CategoryType.EXPENSE.value)),
                default=Value(CategoryType.OPERATIONAL.value),
            )
        )

    def expense_categories(self) -> QuerySet:
        """
        Returns TransferCategory model instances only with EXPENSE category_type.

        Returns:
            QuerySet: Filtered QuerySet containing only EXPENSE TransferCategory type.
        """
        return self.get_queryset().expense_categories()

    def income_categories(self) -> QuerySet:
        """
        Returns TransferCategory model instances only with INCOME category_type.

        Returns:
            QuerySet: Filtered QuerySet containing only INCOME TransferCategory type.
        """
        return self.get_queryset().income_categories()

    def operational_categories(self) -> QuerySet:
        """
        Returns TransferCategory model instances only with INCOME category_type.

        Returns:
            QuerySet: Filtered QuerySet containing only INCOME TransferCategory type.
        """
        return self.get_queryset().operational_categories()
