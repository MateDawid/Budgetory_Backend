import pytest

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType

VALID_TYPE_AND_PRIORITY_COMBINATIONS = (
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.REGULAR,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.REGULAR.label}",
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.IRREGULAR,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.IRREGULAR.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.MOST_IMPORTANT,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.MOST_IMPORTANT.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE, CategoryPriority.DEBTS, id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.DEBTS.label}"
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.SAVINGS,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.SAVINGS.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.OTHERS,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.OTHERS.label}",
    ),
)

INVALID_TYPE_AND_PRIORITY_COMBINATIONS = (
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.REGULAR,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.REGULAR.label}",
    ),
    pytest.param(
        CategoryType.EXPENSE,
        CategoryPriority.IRREGULAR,
        id=f"{CategoryType.EXPENSE.label}-{CategoryPriority.IRREGULAR.label}",
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.MOST_IMPORTANT,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.MOST_IMPORTANT.label}",
    ),
    pytest.param(
        CategoryType.INCOME, CategoryPriority.DEBTS, id=f"{CategoryType.INCOME.label}-{CategoryPriority.DEBTS.label}"
    ),
    pytest.param(
        CategoryType.INCOME,
        CategoryPriority.SAVINGS,
        id=f"{CategoryType.INCOME.label}-{CategoryPriority.SAVINGS.label}",
    ),
    pytest.param(
        CategoryType.INCOME, CategoryPriority.OTHERS, id=f"{CategoryType.INCOME.label}-{CategoryPriority.OTHERS.label}"
    ),
)
