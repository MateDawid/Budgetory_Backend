from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from categories.models.choices.category_type import CategoryType
from predictions.models.expense_prediction_model import ExpensePrediction


@pytest.mark.django_db
class TestExpensePredictionModel:
    """Tests for ExpensePrediction model"""

    PAYLOAD = {
        "current_value": Decimal("100.00"),
        "description": "50.00 for X, 50.00 for Y",
    }

    def test_create_expense_prediction(
        self, budget: Budget, budgeting_period_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances in database. Valid payload for
        ExpensePrediction provided.
        WHEN: ExpensePrediction instance create attempt with valid data.
        THEN: ExpensePrediction model instance exists in database with given data.
        """
        period = budgeting_period_factory(budget=budget)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)

        prediction = ExpensePrediction.objects.create(period=period, category=category, **self.PAYLOAD)

        for key in self.PAYLOAD:
            assert getattr(prediction, key) == self.PAYLOAD[key]
        assert prediction.period == period
        assert prediction.category == category
        assert ExpensePrediction.objects.all().count() == 1
        assert str(prediction) == f"[{prediction.period.name}] {prediction.category.name}"

    @pytest.mark.django_db(transaction=True)
    def test_error_description_too_long(
        self, budget: Budget, budgeting_period_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances in database.
        WHEN: ExpensePrediction instance create attempt with description value too long.
        THEN: DataError raised.
        """
        max_length = ExpensePrediction._meta.get_field("description").max_length
        payload = self.PAYLOAD.copy()
        payload["description"] = (max_length + 1) * "a"
        payload["period"] = budgeting_period_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)

        with pytest.raises(DataError) as exc:
            ExpensePrediction.objects.create(**payload)
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not ExpensePrediction.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field", ("initial_value", "current_value"))
    def test_error_value_too_long(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        field: str,
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances in database.
        WHEN: ExpensePrediction instance create attempt with "value" value too long.
        THEN: DataError raised.
        """
        max_length = (
            ExpensePrediction._meta.get_field(field).max_digits
            - ExpensePrediction._meta.get_field(field).decimal_places
        )
        payload = self.PAYLOAD.copy()
        payload[field] = "1" + "0" * max_length
        payload["period"] = budgeting_period_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)

        with pytest.raises(DataError) as exc:
            ExpensePrediction.objects.create(**payload)
        assert "numeric field overflow" in str(exc.value)
        assert not ExpensePrediction.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field", ("initial_value", "current_value"))
    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_too_low(
        self,
        budget: Budget,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        field: str,
        value: Decimal,
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances in database.
        WHEN: ExpensePrediction instance create attempt with "value" value too low.
        THEN: DataError raised.
        """
        payload = self.PAYLOAD.copy()
        payload[field] = value
        payload["period"] = budgeting_period_factory(budget=budget)
        payload["category"] = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)

        with pytest.raises(IntegrityError) as exc:
            ExpensePrediction.objects.create(**payload)
        assert f'violates check constraint "{field}_gte_0"' in str(exc.value)
        assert not ExpensePrediction.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_on_second_prediction_for_category_in_period(
        self, budget: Budget, budgeting_period_factory: FactoryMetaClass, transfer_category_factory: FactoryMetaClass
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances in database.
        WHEN: Trying to create two ExpensePrediction instances for the same period and category.
        THEN: IntegrityError raised.
        """
        period = budgeting_period_factory(budget=budget)
        category = transfer_category_factory(budget=budget, category_type=CategoryType.EXPENSE)
        ExpensePrediction.objects.create(period=period, category=category, **self.PAYLOAD)

        with pytest.raises(IntegrityError) as exc:
            ExpensePrediction.objects.create(period=period, category=category, **self.PAYLOAD)

        assert "duplicate key value violates unique constraint" in str(exc.value)
        assert ExpensePrediction.objects.all().count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_different_budgets_in_category_and_period(
        self,
        budget_factory: FactoryMetaClass,
        budgeting_period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: BudgetingPeriod and ExpenseCategory models instances for different Budgets in database.
        WHEN: Trying to create ExpensePrediction with period and category in different budgets.
        THEN: ValidationError raised.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        period = budgeting_period_factory(budget=budget_1)
        category = transfer_category_factory(budget=budget_2, category_type=CategoryType.EXPENSE)

        with pytest.raises(ValidationError) as exc:
            ExpensePrediction.objects.create(period=period, category=category, **self.PAYLOAD)

        assert str(exc.value.args[0]) == "Budget for period and category fields is not the same."
        assert not ExpensePrediction.objects.all().exists()
