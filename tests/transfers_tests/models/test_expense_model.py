import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from factory.base import BaseFactory, FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.models.expense_model import Expense
from transfers.models.income_model import Income
from transfers.models.transfer_model import Transfer


@pytest.mark.django_db
class TestExpenseModel:
    """Tests for Expense model"""

    PAYLOAD: dict = {
        "name": "Salary",
        "description": "Salary for this month.",
        "value": Decimal(1000),
    }

    def test_create_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for Expense proxy model.
        WHEN: Expense instance create attempt with valid data.
        THEN: Expense model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT)
        expense = Expense.objects.create(**payload)

        for key in payload:
            assert getattr(expense, key) == payload[key]
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 0
        assert str(expense) == f"{expense.date} | {expense.category} | {expense.value}"

    def test_save_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Valid payload for Expense proxy model.
        WHEN: Expense instance save attempt with valid data.
        THEN: Expense model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.MOST_IMPORTANT)

        expense = Expense(**payload)
        expense.full_clean()
        expense.save()
        expense.refresh_from_db()

        for key in payload:
            assert getattr(expense, key) == payload[key]
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 0
        assert str(expense) == f"{expense.date} | {expense.category} | {expense.value}"

    def test_create_deposit_transfer_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with deposit transfer category. Valid payload for deposit transfer Expense.
        WHEN: Expense instance create attempt with deposit as entity (deposit transfer).
        THEN: Expense and corresponding Income instances created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        source_deposit = deposit_factory(budget=budget)
        target_deposit = deposit_factory(budget=budget)
        payload["entity"] = target_deposit  # Transfer TO this deposit
        payload["deposit"] = source_deposit  # Transfer FROM this deposit
        payload["category"] = transfer_category_factory(
            budget=budget, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )

        # Create deposit income category
        transfer_category_factory(
            budget=budget,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.DEPOSIT_INCOME,
        )

        expense = Expense.objects.create(**payload)

        # Verify expense creation
        for key in payload:
            assert getattr(expense, key) == payload[key]

        # Verify corresponding income creation
        assert hasattr(expense, "deposit_income")
        deposit_income = expense.deposit_income
        assert deposit_income.name == expense.name
        assert deposit_income.description == expense.description
        assert deposit_income.value == expense.value
        assert deposit_income.date == expense.date
        assert deposit_income.period == expense.period
        assert deposit_income.entity == source_deposit  # Income TO source deposit
        assert deposit_income.deposit == target_deposit  # Income FROM target deposit
        assert deposit_income.category.category_type == CategoryType.INCOME
        assert deposit_income.category.priority == CategoryPriority.DEPOSIT_INCOME

        # Verify counts
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Income.objects.filter(period__budget=budget).count() == 1
        assert Transfer.expenses.filter(period__budget=budget).count() == 1
        assert Transfer.incomes.filter(period__budget=budget).count() == 1

    def test_save_deposit_transfer_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget with deposit transfer category. Valid payload for deposit transfer Expense.
        WHEN: Expense instance save attempt with deposit as entity (deposit transfer).
        THEN: Expense and corresponding Income instances exist in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        source_deposit = deposit_factory(budget=budget)
        target_deposit = deposit_factory(budget=budget)
        payload["entity"] = target_deposit
        payload["deposit"] = source_deposit
        payload["category"] = transfer_category_factory(
            budget=budget, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )

        # Create deposit income category
        transfer_category_factory(
            budget=budget,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.DEPOSIT_INCOME,
        )

        expense = Expense(**payload)
        expense.full_clean()
        expense.save()
        expense.refresh_from_db()

        # Verify expense
        for key in payload:
            assert getattr(expense, key) == payload[key]

        # Verify corresponding income
        assert hasattr(expense, "deposit_income")
        deposit_income = expense.deposit_income
        assert deposit_income.name == expense.name
        assert deposit_income.value == expense.value
        assert deposit_income.entity == source_deposit
        assert deposit_income.deposit == target_deposit

        # Verify counts
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Income.objects.filter(period__budget=budget).count() == 1

    def test_update_deposit_transfer_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Existing deposit transfer expense in database.
        WHEN: Expense instance update attempt.
        THEN: Both Expense and corresponding Income instances are updated.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        source_deposit = deposit_factory(budget=budget)
        target_deposit = deposit_factory(budget=budget)
        payload["entity"] = target_deposit
        payload["deposit"] = source_deposit
        payload["category"] = transfer_category_factory(
            budget=budget, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )

        # Create deposit income category
        transfer_category_factory(
            budget=budget,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.DEPOSIT_INCOME,
        )

        # Create initial expense
        expense = Expense.objects.create(**payload)
        initial_income_id = expense.deposit_income.id

        # Update expense
        new_name = "Updated Transfer"
        new_value = Decimal("1500.00")
        expense.name = new_name
        expense.value = new_value
        expense.save()

        # Verify expense update
        expense.refresh_from_db()
        assert expense.name == new_name
        assert expense.value == new_value

        # Verify corresponding income update
        updated_income = Income.objects.get(id=initial_income_id)
        assert updated_income.name == new_name
        assert updated_income.value == new_value

        # Verify counts remain the same
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Income.objects.filter(period__budget=budget).count() == 1

    def test_delete_deposit_transfer_expense(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Existing deposit transfer expense in database.
        WHEN: Expense instance delete attempt.
        THEN: Both Expense and corresponding Income instances are deleted.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        source_deposit = deposit_factory(budget=budget)
        target_deposit = deposit_factory(budget=budget)
        payload["entity"] = target_deposit
        payload["deposit"] = source_deposit
        payload["category"] = transfer_category_factory(
            budget=budget, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )

        # Create deposit income category
        transfer_category_factory(
            budget=budget,
            category_type=CategoryType.INCOME,
            priority=CategoryPriority.DEPOSIT_INCOME,
        )

        # Create expense
        expense = Expense.objects.create(**payload)
        income_id = expense.deposit_income.id

        # Verify both records exist
        assert Expense.objects.filter(period__budget=budget).count() == 1
        assert Income.objects.filter(period__budget=budget).count() == 1
        assert Income.objects.filter(id=income_id).exists()

        # Delete expense
        expense.delete()

        # Verify both records are deleted
        assert Expense.objects.filter(period__budget=budget).count() == 0
        assert Income.objects.filter(period__budget=budget).count() == 0
        assert not Income.objects.filter(id=income_id).exists()

    def test_error_missing_deposit_income_category_for_deposit_transfer(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget without deposit income category. Valid payload for deposit transfer Expense.
        WHEN: Expense instance create attempt with deposit as entity.
        THEN: Exception raised due to missing deposit income category.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        source_deposit = deposit_factory(budget=budget)
        target_deposit = deposit_factory(budget=budget)
        payload["entity"] = target_deposit
        payload["deposit"] = source_deposit
        payload["category"] = transfer_category_factory(
            budget=budget, category_type=CategoryType.EXPENSE, priority=CategoryPriority.MOST_IMPORTANT
        )

        # Don't create deposit income category - this should cause an error

        with pytest.raises(Exception):  # Could be DoesNotExist or other exception
            Expense.objects.create(**payload)

        # Verify no records were created
        assert Expense.objects.filter(period__budget=budget).count() == 0
        assert Income.objects.filter(period__budget=budget).count() == 0

    def test_error_on_create_expense_with_income_category(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Invalid payload for Expense proxy model.
        WHEN: Expense instance create attempt with Income category in payload.
        THEN: ValidationError raised. Expense not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)

        with pytest.raises(ValidationError) as exc:
            Expense.objects.create(**payload)
        assert str(exc.value.error_list[0].message) == "Expense model instance can not be created with IncomeCategory."
        assert not Expense.objects.all().exists()

    def test_error_on_save_expense_with_expense_category(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Budget model instance in database. Invalid payload for Expense proxy model.
        WHEN: Expense instance save attempt with Income category in payload.
        THEN: ValidationError raised. Expense not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(budget=budget)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, priority=CategoryPriority.REGULAR)

        with pytest.raises(ValidationError) as exc:
            expense = Expense(**payload)
            expense.full_clean()
            expense.save()
        assert str(exc.value.error_list[0].message) == "Expense model instance can not be created with IncomeCategory."
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name", "description"])
    def test_error_value_too_long(self, budget: Budget, expense_factory: BaseFactory, field_name: str):
        """
        GIVEN: Payload with too long value for one field.
        WHEN: Expense instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = Expense._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"
        expense = expense_factory.build(budget=budget, **payload)

        with pytest.raises(DataError) as exc:
            expense.save()
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Expense.objects.filter(period__budget=budget).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_too_low(
        self,
        budget: Budget,
        expense_factory: BaseFactory,
        value: Decimal,
    ):
        """
        GIVEN: Payload with invalid "value" field value.
        WHEN: Expense instance create attempt with "value" value too low.
        THEN: IntegrityError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["value"] = value
        expense = expense_factory.build(budget=budget, **payload)

        with pytest.raises(IntegrityError) as exc:
            expense.save()
        assert 'violates check constraint "transfers_transfer_value_gt_0"' in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_deposit_and_entity_the_same(
        self,
        budget: Budget,
        expense_factory: BaseFactory,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Payload with the same value for "deposit" and "entity" fields.
        WHEN: Expense instance create attempt.
        THEN: IntegrityError raised.
        """
        payload = self.PAYLOAD.copy()
        deposit = deposit_factory(budget=budget)
        payload["deposit"] = deposit
        payload["entity"] = deposit
        expense = expense_factory.build(budget=budget, **payload)
        with pytest.raises(IntegrityError) as exc:
            expense.save()
        assert 'violates check constraint "transfers_transfer_deposit_and_entity_not_the_same"' in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.parametrize(
        "date",
        (
            datetime.date(year=2024, month=9, day=10),
            datetime.date(year=2024, month=9, day=30),
            datetime.date(year=2024, month=11, day=1),
        ),
    )
    @pytest.mark.django_db(transaction=True)
    def test_error_expense_date_out_of_period(
        self,
        budget: Budget,
        expense_factory: BaseFactory,
        budgeting_period_factory: FactoryMetaClass,
        date: datetime.date,
    ):
        """
        GIVEN: Payload with Expense "date" not in given "period" date range.
        WHEN: Expense instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = date
        payload["period"] = budgeting_period_factory(
            budget=budget, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31)
        )

        expense = expense_factory.build(budget=budget, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()

        assert "Transfer date not in period date range." in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_entity_in_deposit_field(
        self, budget: Budget, expense_factory: BaseFactory, entity_factory: FactoryMetaClass
    ):
        """
        GIVEN: Payload with Entity instance as "deposit" field value.
        WHEN: Expense instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["deposit"] = entity_factory(budget=budget)
        payload["entity"] = entity_factory(budget=budget)
        expense = expense_factory.build(budget=budget, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()
        assert 'Value of "deposit" field has to be Deposit model instance.' in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.parametrize("field", ["period", "category", "entity", "deposit"])
    @pytest.mark.django_db(transaction=True)
    def test_error_different_budgets_in_category_and_period(
        self,
        budget_factory: FactoryMetaClass,
        expense_factory: BaseFactory,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        field: str,
    ):
        """
        GIVEN: Two Budgets in database. Payload with one of period, category, entity and deposit value with
        other Budget than others.
        WHEN: Create Expense in database.
        THEN: ValidationError raised.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        payload = self.PAYLOAD.copy()
        match field:
            case "period":
                payload[field] = budgeting_period_factory(budget=budget_2)
            case "category":
                payload[field] = transfer_category_factory(budget=budget_2, category_type=CategoryType.EXPENSE)
            case "entity":
                payload[field] = entity_factory(budget=budget_2)
            case "deposit":
                payload[field] = deposit_factory(budget=budget_2)

        expense = expense_factory.build(budget=budget_1, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()

        assert str(exc.value.args[0]) == "Budget for period, category, entity and deposit fields is not the same."
        assert not Expense.objects.all().exists()
