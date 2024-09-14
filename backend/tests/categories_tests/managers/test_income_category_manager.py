import pytest
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.transfer_category_choices import CategoryType, IncomeCategoryPriority
from categories.models.transfer_category_model import TransferCategory


@pytest.mark.django_db
class TestIncomeCategoryManager:
    """Tests for IncomeCategoryManager."""

    def test_get_queryset(
        self, budget: Budget, transfer_category_factory: FactoryMetaClass, income_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: Budget and two TransferCategories (one with category_type=CategoryType.INCOME and one with
        category_type=CategoryType.INCOME) models instances in database.
        WHEN: Calling IncomeCategoryManager for get_queryset.
        THEN: Manager returns only object with category_type=CategoryType.INCOME.
        """
        transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        income_category = income_category_factory(budget=budget)

        qs = TransferCategory.income_categories.all()

        assert TransferCategory.objects.all().count() == 2
        assert qs.count() == 1
        assert income_category in qs

    def test_create(self, budget: Budget):
        """
        GIVEN: Budget model instance in database.
        WHEN: Calling IncomeCategoryManager for create.
        THEN: Manager creates object always with category_type set to CategoryType.INCOME.
        """

        payload = {
            "budget": budget,
            "name": "Income",
            "description": "Category for income.",
            "is_active": True,
            "category_type": CategoryType.EXPENSE,  # intentionally set to CategoryType.EXPENSE
            "priority": IncomeCategoryPriority.REGULAR,
        }

        category = TransferCategory.income_categories.create(**payload)

        assert category.category_type == CategoryType.INCOME
        for param in payload:
            if param == "category_type":
                continue
            assert getattr(category, param) == payload[param]

    def test_update(self, transfer_category_factory: FactoryMetaClass):
        """
        GIVEN: Budget model instance in database.
        WHEN: Calling IncomeCategoryManager for update.
        THEN: Manager updates object always with category_type set to CategoryType.INCOME.
        """
        entity = transfer_category_factory(category_type=CategoryType.INCOME)
        assert TransferCategory.income_categories.all().count() == 1

        TransferCategory.income_categories.update(category_type=CategoryType.EXPENSE)

        entity.refresh_from_db()
        assert TransferCategory.income_categories.all().count() == 1
        assert entity.category_type == CategoryType.INCOME
