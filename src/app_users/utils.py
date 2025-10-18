from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType


def create_initial_categories_for_budget_pk(budget_pk: int) -> None:
    """
    Function creating predefined TransferCategories for Budget with given PK.

    Args:
        budget_pk (int): Budget PK.
    """
    initial_categories = [
        TransferCategory(
            budget_id=budget_pk, name="Salary", category_type=CategoryType.INCOME, priority=CategoryPriority.REGULAR
        ),
        TransferCategory(
            budget_id=budget_pk, name="Sell", category_type=CategoryType.INCOME, priority=CategoryPriority.IRREGULAR
        ),
        TransferCategory(
            budget_id=budget_pk,
            name="Bills",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        ),
        TransferCategory(
            budget_id=budget_pk,
            name="Food",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        ),
        TransferCategory(
            budget_id=budget_pk, name="Savings", category_type=CategoryType.EXPENSE, priority=CategoryPriority.SAVINGS
        ),
        TransferCategory(
            budget_id=budget_pk,
            name="Entertainment",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        ),
    ]
    TransferCategory.objects.bulk_create(initial_categories)
