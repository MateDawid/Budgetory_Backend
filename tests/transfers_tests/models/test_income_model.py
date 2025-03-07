import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from factory.base import BaseFactory, FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_priority import CategoryPriority
from transfers.models.income_model import Income
from transfers.models.transfer_model import Transfer


@pytest.mark.django_db
class TestIncomeModel:
    """Tests for Income model"""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_create_income(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for Income proxy model.
        WHEN: Income instance create attempt with valid data.
        THEN: Income model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)
        income = Income.objects.create(**payload)

        for key in payload:
            assert getattr(income, key) == payload[key]
        assert Income.objects.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 0
        assert str(income) == f"{income.date} | {income.category} | {income.value}"

    def test_save_income(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for Income proxy model.
        WHEN: Income instance save attempt with valid data.
        THEN: Income model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)

        income = Income(**payload)
        income.full_clean()
        income.save()
        income.refresh_from_db()

        for key in payload:
            assert getattr(income, key) == payload[key]
        assert Income.objects.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 0
        assert str(income) == f"{income.date} | {income.category} | {income.value}"

    def test_error_on_create_income_with_expense_category(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Invalid payload for Income proxy model.
        WHEN: Income instance create attempt with Expense category in payload.
        THEN: ValidationError raised. Income not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT)

        with pytest.raises(ValidationError) as exc:
            Income.objects.create(**payload)
        assert str(exc.value.error_list[0].message) == "Income model instance can not be created with ExpenseCategory."
        assert not Income.objects.all().exists()

    def test_error_on_save_income_with_expense_category(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Invalid payload for Income proxy model.
        WHEN: Income instance save attempt with Expense category in payload.
        THEN: ValidationError raised. Income not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30), is_active=True
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT)

        with pytest.raises(ValidationError) as exc:
            income = Income(**payload)
            income.full_clean()
            income.save()
        assert str(exc.value.error_list[0].message) == "Income model instance can not be created with ExpenseCategory."
        assert not Income.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, budget: Budget, income_factory: BaseFactory, field_name: str):
        """
        GIVEN: Payload with too long value for one field.
        WHEN: Income instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = Income._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"
        income = income_factory.build(budget=budget, **payload)

        with pytest.raises(DataError) as exc:
            income.save()
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Income.objects.filter(period__budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_too_low(
        self,
        budget: Budget,
        income_factory: BaseFactory,
        value: Decimal,
    ):
        """
        GIVEN: Payload with invalid "value" field value.
        WHEN: Income instance create attempt with "value" value too low.
        THEN: IntegrityError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["value"] = value
        income = income_factory.build(budget=budget, **payload)

        with pytest.raises(IntegrityError) as exc:
            income.save()
        assert 'violates check constraint "transfers_transfer_value_gt_0"' in str(exc.value)
        assert not Income.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_deposit_and_entity_the_same(
        self,
        budget: Budget,
        income_factory: BaseFactory,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Payload with the same value for "deposit" and "entity" fields.
        WHEN: Income instance create attempt.
        THEN: IntegrityError raised.
        """
        payload = self.PAYLOAD.copy()
        deposit = deposit_factory(budget=budget)
        payload["deposit"] = deposit
        payload["entity"] = deposit
        income = income_factory.build(budget=budget, **payload)
        with pytest.raises(IntegrityError) as exc:
            income.save()
        assert 'violates check constraint "transfers_transfer_deposit_and_entity_not_the_same"' in str(exc.value)
        assert not Income.objects.all().exists()

    @pytest.mark.parametrize(
        "date",
        (
            datetime.date(year=2024, month=9, day=10),
            datetime.date(year=2024, month=9, day=30),
            datetime.date(year=2024, month=11, day=1),
        ),
    )
    @pytest.mark.django_db(transaction=True)
    def test_error_income_date_out_of_period(
        self,
        budget: Budget,
        income_factory: BaseFactory,
        budgeting_period_factory: FactoryMetaClass,
        date: datetime.date,
    ):
        """
        GIVEN: Payload with Income "date" not in given "period" date range.
        WHEN: Income instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = date
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31), is_active=True
        )

        income = income_factory.build(budget=budget, **payload)
        with pytest.raises(ValidationError) as exc:
            income.save()

        assert "Transfer date not in period date range." in str(exc.value)
        assert not Income.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_entity_in_deposit_field(
        self, budget: Budget, income_factory: BaseFactory, entity_factory: FactoryMetaClass
    ):
        """
        GIVEN: Payload with Entity instance as "deposit" field value.
        WHEN: Income instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["deposit"] = entity_factory(budget=budget)
        payload["entity"] = entity_factory(budget=budget)
        income = income_factory.build(budget=budget, **payload)
        with pytest.raises(ValidationError) as exc:
            income.save()
        assert 'Value of "deposit" field has to be Deposit model instance.' in str(exc.value)
        assert not Income.objects.all().exists()

    @pytest.mark.parametrize("field", ["period", "category", "entity", "deposit"])
    @pytest.mark.django_db(transaction=True)
    def test_error_different_budgets_in_category_and_period(
        self,
        budget_factory: FactoryMetaClass,
        income_factory: BaseFactory,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        field: str,
    ):
        """
        GIVEN: Two Budgets in database. Payload with one of period, category, entity and deposit value with
        other Budget than others.
        WHEN: Create Income in database.
        THEN: ValidationError raised.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = self.PAYLOAD.copy()
        match field:
            case "period":
                payload[field] = budgeting_period_factory(budget=budget_2)
            case "category":
                payload[field] = transfer_category_factory(budget=budget_2)
            case "entity":
                payload[field] = entity_factory(budget=budget_2)
            case "deposit":
                payload[field] = deposit_factory(budget=budget_2)

        income = income_factory.build(budget=budget_1, **payload)
        with pytest.raises(ValidationError) as exc:
            income.save()

        assert str(exc.value.args[0]) == "Budget for period, category, entity and deposit fields is not the same."
        assert not Income.objects.all().exists()
