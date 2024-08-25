import pytest
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models import TransferCategory
from categories.models.category_priority_choices import CategoryPriority
from categories.models.category_type_choices import CategoryType


@pytest.mark.django_db
class TestExpenseCategoryManager:
    """Tests for ExpenseCategoryManager."""

    def test_get_queryset(
        self, budget: Budget, transfer_category_factory: FactoryMetaClass, expense_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget and two TransferCategories (one with category_type=CategoryType.INCOME and one with
        category_type=CategoryType.EXPENSE) models instances in database.
        WHEN: Calling ExpenseCategoryManager for get_queryset.
        THEN: Manager returns only object with category_type=CategoryType.EXPENSE.
        """
        transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)
        expense_category = expense_category_factory(budget=budget)

        qs = TransferCategory.expense_categories.all()

        assert TransferCategory.objects.all().count() == 2
        assert qs.count() == 1
        assert expense_category in qs

    def test_create(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Calling ExpenseCategoryManager for create.
        THEN: Manager creates object always with category_type set to CategoryType.EXPENSE.
        """

        payload = {
            "budget": budget,
            "name": "Expense",
            "description": "Category for expense.",
            "is_active": True,
            "category_type": CategoryType.INCOME,  # intentionally set to CategoryType.INCOME
            "priority": CategoryPriority.MOST_IMPORTANT,
        }

        category = TransferCategory.expense_categories.create(**payload)

        assert category.category_type == CategoryType.EXPENSE
        for param in payload:
            if param == "category_type":
                continue
            assert getattr(category, param) == payload[param]

    def test_update(self, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: Calling ExpenseCategoryManager for update.
        THEN: Manager updates object always with category_type set to CategoryType.EXPENSE.
        """
        entity = transfer_category_factory(category_type=CategoryType.EXPENSE)
        assert TransferCategory.expense_categories.all().count() == 1

        TransferCategory.expense_categories.update(category_type=CategoryType.INCOME)

        entity.refresh_from_db()
        assert TransferCategory.expense_categories.all().count() == 1
        assert entity.category_type == CategoryType.EXPENSE
