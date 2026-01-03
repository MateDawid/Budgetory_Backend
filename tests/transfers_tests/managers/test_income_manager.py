import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from factory.base import FactoryMetaClass

from categories.models.choices.category_priority import CategoryPriority
from categories.models.choices.category_type import CategoryType
from transfers.models.transfer_model import Transfer
from wallets.models.wallet_model import Wallet


@pytest.mark.django_db
class TestIncomeManager:
    """Tests for IncomeManager."""

    PAYLOAD = {
        "name": "Salary",
        "description": "Monthly salary.",
        "value": Decimal(1000),
        "date": datetime.date(year=2024, month=9, day=1),
    }

    def test_get_queryset(self, wallet: Wallet, expense_factory: FactoryMetaClass, income_factory: FactoryMetaClass):
        """
        GIVEN: Wallet and two Transfers (one Expense and one Income) models instances in database.
        WHEN: Calling IncomeManager for get_queryset.
        THEN: Manager returns only Income proxy model instances.
        """
        expense_factory(wallet=wallet)
        income = income_factory(wallet=wallet)

        qs = Transfer.incomes.all()

        assert Transfer.objects.all().count() == 2
        assert qs.count() == 1
        assert income in qs

    def test_create(
        self,
        wallet: Wallet,
        period_factory: FactoryMetaClass,
        entity_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        transfer_category_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Valid payload for Income proxy model.
        WHEN: Calling IncomeManager for create.
        THEN: Income proxy model created in database.
        """
        payload = self.PAYLOAD.copy()
        payload["period"] = period_factory(
            wallet=wallet, date_start=datetime.date(2024, 9, 1), date_end=datetime.date(2024, 9, 30)
        )
        payload["entity"] = entity_factory(wallet=wallet)
        payload["deposit"] = deposit_factory(wallet=wallet)
        payload["category"] = transfer_category_factory(wallet=wallet, priority=CategoryPriority.REGULAR)

        transfer = Transfer.incomes.create(**payload)

        for param in payload:
            assert getattr(transfer, param) == payload[param]
        assert Transfer.objects.filter(period__wallet=wallet).count() == 1
        assert Transfer.incomes.filter(period__wallet=wallet).count() == 1
        assert Transfer.expenses.filter(period__wallet=wallet).count() == 0
        assert str(transfer) == f"{transfer.date} | {transfer.category} | {transfer.value}"

    def test_update(
        self, wallet: Wallet, transfer_category_factory: FactoryMetaClass, transfer_factory: FactoryMetaClass
    ):
        """
        GIVEN: Valid payload for Income proxy model.
        WHEN: Calling IncomeManager for update.
        THEN: Income proxy model updated in database.
        """

        transfer = transfer_factory(
            wallet=wallet, category=transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)
        )
        assert Transfer.incomes.all().count() == 1
        new_category = transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)

        Transfer.incomes.filter(pk=transfer.pk).update(category=new_category)

        transfer.refresh_from_db()
        assert Transfer.incomes.all().count() == 1
        assert transfer.category == new_category

    def test_error_on_update_with_expense_category(
        self,
        wallet: Wallet,
        transfer_category_factory: FactoryMetaClass,
        transfer_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Invalid payload for Income proxy model with ExpenseCategory in "category" field.
        WHEN: Calling IncomeManager for update.
        THEN: ValidationError raised, Income proxy model not updated in database.
        """
        valid_category = transfer_category_factory(wallet=wallet, category_type=CategoryType.INCOME)
        transfer = transfer_factory(wallet=wallet, category=valid_category)
        assert Transfer.incomes.all().count() == 1
        invalid_category = transfer_category_factory(wallet=wallet, category_type=CategoryType.EXPENSE)

        with pytest.raises(ValidationError) as exc:
            Transfer.incomes.filter(pk=transfer.pk).update(category=invalid_category)
        assert str(exc.value.error_list[0].message) == "Income model instance can not be created with ExpenseCategory."
        transfer.refresh_from_db()
        assert transfer.category == valid_category
