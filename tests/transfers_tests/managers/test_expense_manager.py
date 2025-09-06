import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.models.transfer_model import Transfer


@pytest.mark.django_db
class TestExpenseManager:
    """Tests for ExpenseManager."""

    PAYLOAD = {
        "name": "Flat rent",
        "description": "Payment for flat rent.",
        "value": Decimal(900),
        "date": datetime.date(year=2024, month=9, day=10),
    }

    def test_get_queryset(self, budget: Budget, expense_factory: FactoryMetaClass, income_factory: FactoryMetaClass):
        """
        GIVEN: Budget and two Transfers (one Expense and one Income) models instances in database.
        WHEN: Calling ExpenseManager for get_queryset.
        THEN: Manager returns only Expense proxy model instances.
        """
        income_factory(budget=budget)
        expense = expense_factory(budget=budget)

        qs = Transfer.expenses.all()

        assert Transfer.objects.all().count() == 2
        assert qs.count() == 1
        assert expense in qs

    def test_create(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Valid payload for Expense proxy model.
        WHEN: Calling ExpenseManager for create.
        THEN: Expense proxy model created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT)

        transfer = Transfer.expenses.create(**payload)

        for param in payload:
            assert getattr(transfer, param) == payload[param]
        assert Transfer.objects.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 0
        assert str(transfer) == f"{transfer.date} | {transfer.category} | {transfer.value}"

    def test_update(
        self, budget: Budget, transfer_category_factory: FactoryMetaClass, transfer_factory: FactoryMetaClass
    ):
        """
        GIVEN: Valid payload for Expense proxy model.
        WHEN: Calling ExpenseManager for update.
        THEN: Expense proxy model updated in database.
        """

        transfer = transfer_factory(
            budget=budget, category=transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        )
        assert Transfer.expenses.all().count() == 1
        new_category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)

        Transfer.expenses.filter(pk=transfer.pk).update(category=new_category)

        transfer.refresh_from_db()
        assert Transfer.expenses.all().count() == 1
        assert transfer.category == new_category

    def test_error_on_update_with_income_category(
        self,
        budget: Budget,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Invalid payload for Expense proxy model with IncomeCategory in "category" field.
        WHEN: Calling ExpenseManager for update.
        THEN: ValidationError raised, Expense proxy model not updated in database.
        """
        valid_category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        transfer = transfer_factory(budget=budget, category=valid_category)
        assert Transfer.expenses.all().count() == 1
        invalid_category = transfer_category_factory(budget=budget, category_type=CategoryType.INCOME)

        with pytest.raises(ValidationError) as exc:
            Transfer.expenses.filter(pk=transfer.pk).update(category=invalid_category)
        assert str(exc.value.error_list[0].message) == "Expense model instance can not be created with IncomeCategory."
        transfer.refresh_from_db()
        assert transfer.category == valid_category
