from categories.models import TransferCategory
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType


def create_initial_categories_for_daily_expenses_deposit(budget_pk: int, deposit_pk: int) -> None:
    """
    Function creating predefined TransferCategories for Daily Expenses type Deposit with given PK.

    Args:
        budget_pk (int): Budget PK.
        deposit_pk (int): Deposit PK.
    """
    initial_categories = [
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Salary",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Sell",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.IRREGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Bills",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For Savings",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.SAVINGS,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For Investments",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.SAVINGS,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Entertainment",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        ),
    ]
    TransferCategory.objects.bulk_create(initial_categories)


def create_initial_categories_for_savings_and_investments_deposit(budget_pk: int, deposit_pk: int) -> None:
    """
    Function creating predefined TransferCategories for Savings and Investments types of Deposit with given PK.

    Args:
        budget_pk (int): Budget PK.
        deposit_pk (int): Deposit PK.
    """
    initial_categories = [
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Income from User",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Value increase",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Value decrease",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Funds withdrawal",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        ),
    ]
    TransferCategory.objects.bulk_create(initial_categories)


def create_initial_categories_for_other_deposit(budget_pk: int, deposit_pk: int) -> None:
    """
    Function creating predefined TransferCategories for Other type Deposit with given PK.

    Args:
        budget_pk (int): Budget PK.
        deposit_pk (int): Deposit PK.
    """
    initial_categories = [
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Regular income",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.REGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="Irregular income",
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.IRREGULAR,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For most important expenses",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.MOST_IMPORTANT,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For savings",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.SAVINGS,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For investments",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.SAVINGS,
        ),
        TransferCategory(
            budget_id=budget_pk,
            deposit_id=deposit_pk,
            name="For other expenses",
            category_type=CategoryType.EXPENSE,
            priority=CategoryPriority.OTHERS,
        ),
    ]
    TransferCategory.objects.bulk_create(initial_categories)
