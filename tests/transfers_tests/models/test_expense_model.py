import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import DataError, IntegrityError
from factory.base import BaseFactory, FactoryMetaClass

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.models.expense_model import Expense
from transfers.models.transfer_model import Transfer
from wallets.models.wallet_model import Wallet


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
        wallet: Wallet,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database. Valid payload for Expense proxy model.
        WHEN: Expense instance create attempt with valid data.
        THEN: Expense model instance created in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, priority=CategoryPriority.MOST_IMPORTANT)
        expense = Expense.objects.create(**payload)

        for key in payload:
            assert getattr(expense, key) == payload[key]
        assert Expense.objects.filter(period__wallet=wallet).count() == 1
        assert Transfer.expenses.filter(period__wallet=wallet).count() == 1
        assert Transfer.incomes.filter(period__wallet=wallet).count() == 0
        assert str(expense) == f"{expense.date} | {expense.category} | {expense.value}"

    def test_save_expense(
        self,
        wallet: Wallet,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database. Valid payload for Expense proxy model.
        WHEN: Expense instance save attempt with valid data.
        THEN: Expense model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, priority=CategoryPriority.MOST_IMPORTANT)

        expense = Expense(**payload)
        expense.full_clean(exclude=["transfer_type"])
        expense.save()
        expense.refresh_from_db()

        for key in payload:
            assert getattr(expense, key) == payload[key]
        assert Expense.objects.filter(period__wallet=wallet).count() == 1
        assert Transfer.expenses.filter(period__wallet=wallet).count() == 1
        assert Transfer.incomes.filter(period__wallet=wallet).count() == 0
        assert str(expense) == f"{expense.date} | {expense.category} | {expense.value}"

    def test_error_on_create_expense_with_income_category(
        self,
        wallet: Wallet,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database. Invalid payload for Expense proxy model.
        WHEN: Expense instance create attempt with Income category in payload.
        THEN: ValidationError raised. Expense not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, priority=CategoryPriority.REGULAR)

        with pytest.raises(ValidationError) as exc:
            Expense.objects.create(**payload)
        assert str(exc.value.error_list[0].message) == "Expense model instance can not be created with IncomeCategory."
        assert not Expense.objects.all().exists()

    def test_error_on_save_expense_with_expense_category(
        self,
        wallet: Wallet,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Wallet model instance in database. Invalid payload for Expense proxy model.
        WHEN: Expense instance save attempt with Income category in payload.
        THEN: ValidationError raised. Expense not created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = datetime.date(2024, 9, 1)
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, priority=CategoryPriority.REGULAR)

        with pytest.raises(ValidationError) as exc:
            expense = Expense(**payload)
            expense.full_clean(exclude=["transfer_type"])
            expense.save()
        assert str(exc.value.error_list[0].message) == "Expense model instance can not be created with IncomeCategory."
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("field_name", ["name"])
    def test_error_value_too_long(self, wallet: Wallet, expense_factory: BaseFactory, field_name: str):
        """
        GIVEN: Payload with too long value for one field.
        WHEN: Expense instance create attempt with field value too long.
        THEN: DataError raised.
        """
        max_length = Expense._meta.get_field(field_name).max_length
        payload = self.PAYLOAD.copy()
        payload[field_name] = (max_length + 1) * "a"
        expense = expense_factory.build(wallet=wallet, **payload)

        with pytest.raises(DataError) as exc:
            expense.save()
        assert str(exc.value) == f"value too long for type character varying({max_length})\n"
        assert not Expense.objects.filter(period__wallet=wallet).exists()

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.parametrize("value", [Decimal("0.00"), Decimal("-0.01")])
    def test_error_value_too_low(
        self,
        wallet: Wallet,
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
        expense = expense_factory.build(wallet=wallet, **payload)

        with pytest.raises(IntegrityError) as exc:
            expense.save()
        assert 'violates check constraint "transfers_transfer_value_gt_0"' in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_deposit_and_entity_the_same(
        self,
        wallet: Wallet,
        expense_factory: BaseFactory,
        deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Payload with the same value for "deposit" and "entity" fields.
        WHEN: Expense instance create attempt.
        THEN: IntegrityError raised.
        """
        payload = self.PAYLOAD.copy()
        deposit = deposit_factory(wallet=wallet)
        payload["deposit"] = deposit
        payload["entity"] = deposit
        expense = expense_factory.build(wallet=wallet, **payload)
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
        wallet: Wallet,
        expense_factory: BaseFactory,
        period_factory: FactoryMetaClass,
        date: datetime.date,
    ):
        """
        GIVEN: Payload with Expense "date" not in given "period" date range.
        WHEN: Expense instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["date"] = date
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 10, 1), date_end=datetime.date(2024, 10, 31)
        )

        expense = expense_factory.build(wallet=wallet, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()

        assert "Transfer date not in period date range." in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_entity_in_deposit_field(
        self, wallet: Wallet, expense_factory: BaseFactory, entity_factory: FactoryMetaClass
    ):
        """
        GIVEN: Payload with Entity instance as "deposit" field value.
        WHEN: Expense instance create attempt.
        THEN: ValidationError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["deposit"] = entity_factory(wallet=wallet)
        payload["entity"] = entity_factory(wallet=wallet)
        expense = expense_factory.build(wallet=wallet, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()
        assert 'Value of "deposit" field has to be Deposit model instance.' in str(exc.value)
        assert not Expense.objects.all().exists()

    @pytest.mark.parametrize("field", ["period", "category", "entity", "deposit"])
    @pytest.mark.django_db(transaction=True)
    def test_error_different_wallets_in_category_and_period(
        self,
        wallet_factory: FactoryMetaClass,
        expense_factory: BaseFactory,
        period_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        field: str,
    ):
        """
        GIVEN: Two Wallets in database. Payload with one of period, category, entity and deposit value with
        other Wallet than others.
        WHEN: Create Expense in database.
        THEN: ValidationError raised.
        """
        wallet_1 = wallet_factory()
        wallet_2 = wallet_factory()
        payload = self.PAYLOAD.copy()
        match field:
            case "period":
                payload[field] = period_factory(wallet=wallet_2)
            case "category":
                payload[field] = transfer_category_factory(wallet=wallet_2, category_type=CategoryType.EXPENSE)
            case "entity":
                payload[field] = entity_factory(wallet=wallet_2)
            case "deposit":
                payload[field] = deposit_factory(wallet=wallet_2)

        expense = expense_factory.build(wallet=wallet_1, **payload)
        with pytest.raises(ValidationError) as exc:
            expense.save()

        assert str(exc.value.args[0]) == "Wallet for period, category, entity and deposit fields is not the same."
        assert not Expense.objects.all().exists()
