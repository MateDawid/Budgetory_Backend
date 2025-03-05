import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.transfer_category_choices import IncomeCategoryPriority
from transfers.models.transfer_model import Transfer


@pytest.mark.django_db
class TestIncomeManager:
    """Tests for IncomeManager."""

    PAYLOAD = {
        "name": "Salary",
        "description": "Monthly salary.",
        "value": Decimal(1000),
        "date": datetime.date(year=2024, month=9, day=1),
    }

    def test_get_queryset(self, budget: Budget, expense_factory: FactoryMetaClass, income_factory: FactoryMetaClass):
        """
        GIVEN: Budget and two Transfers (one Expense and one Income) models instances in database.
        WHEN: Calling IncomeManager for get_queryset.
        THEN: Manager returns only Income proxy model instances.
        """
        expense_factory(budget=budget)
        income = income_factory(budget=budget)

        qs = Transfer.incomes.all()

        assert Transfer.objects.all().count() == 2
        assert qs.count() == 1
        assert income in qs

    def test_create(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Valid payload for Income proxy model.
        WHEN: Calling IncomeManager for create.
        THEN: Income proxy model created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = income_category_factory(budget=budget, priority=IncomeCategoryPriority.REGULAR)

        transfer = Transfer.incomes.create(**payload)

        for param in payload:
            assert getattr(transfer, param) == payload[param]
        assert Transfer.objects.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 0
        assert str(transfer) == f"{transfer.date} | {transfer.category} | {transfer.value}"

    def test_error_on_create_with_expense_category(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        expense_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Invalid payload for Income proxy model with IncomeCategory in "category" field.
        WHEN: Calling IncomeManager for create.
        THEN: ValidationError raised, Income proxy model not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = expense_category_factory(budget=budget)

        with pytest.raises(ValidationError) as exc:
            Transfer.incomes.create(**payload)
        assert str(exc.value.error_list[0].message) == "Income model instance can not be created with ExpenseCategory."
        assert not Transfer.incomes.all().exists()

    def test_update(
        self, budget: Budget, income_category_factory: FactoryMetaClass, transfer_factory: FactoryMetaClass
    ):
        """
        GIVEN: Valid payload for Income proxy model.
        WHEN: Calling IncomeManager for update.
        THEN: Income proxy model updated in database.
        """

        transfer = transfer_factory(budget=budget, category=income_category_factory(budget=budget))
        assert Transfer.incomes.all().count() == 1
        new_category = income_category_factory(budget=budget)

        Transfer.incomes.filter(pk=transfer.pk).update(category=new_category)

        transfer.refresh_from_db()
        assert Transfer.incomes.all().count() == 1
        assert transfer.category == new_category

    def test_error_on_update_with_income_category(
        self,
        budget: Budget,
        expense_category_factory: FactoryMetaClass,
        income_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Invalid payload for Income proxy model with ExpenseCategory in "category" field.
        WHEN: Calling IncomeManager for update.
        THEN: ValidationError raised, Income proxy model not updated in database.
        """
        valid_category = income_category_factory(budget=budget)
        transfer = transfer_factory(budget=budget, category=valid_category)
        assert Transfer.incomes.all().count() == 1
        invalid_category = expense_category_factory(budget=budget)

        with pytest.raises(ValidationError) as exc:
            Transfer.incomes.filter(pk=transfer.pk).update(category=invalid_category)
        assert str(exc.value.error_list[0].message) == "Income model instance can not be created with ExpenseCategory."
        transfer.refresh_from_db()
        assert transfer.category == valid_category
