from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from factory.base import FactoryMetaClass

from budgets.models.budget_model import Budget
from wallets.models.wallet_deposit_model import WalletDeposit


@pytest.mark.django_db
class TestWalletDepositModel:
    """Tests for WalletDeposit model"""

    PAYLOAD = {
        "planned_weight": Decimal("50.00"),
    }

    def test_create_wallet_deposit(
        self, budget: Budget, deposit_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit and Wallet models instances in database. Valid payload for WalletDeposit provided.
        WHEN: WalletDeposit instance create attempt with valid data.
        THEN: WalletDeposit model instance exists in database with given data.
        """
        payload = self.PAYLOAD.copy()
        payload["deposit"] = deposit_factory(budget=budget)
        payload["wallet"] = wallet_factory(budget=budget)

        wallet_deposit = WalletDeposit.objects.create(**payload)

        for key in payload:
            assert getattr(wallet_deposit, key) == payload[key]
        assert WalletDeposit.objects.all().count() == 1
        assert str(wallet_deposit) == f"{wallet_deposit.deposit.name} ({wallet_deposit.wallet.name})"

    @pytest.mark.django_db(transaction=True)
    def test_error_planned_weight_too_long(
        self, budget: Budget, deposit_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit and Wallet models instances in database. Valid payload for WalletDeposit provided.
        WHEN: WalletDeposit instance create attempt with "value" value too long.
        THEN: DataError raised.
        """
        max_length = (
            WalletDeposit._meta.get_field("planned_weight").max_digits
            - WalletDeposit._meta.get_field("planned_weight").decimal_places
        )
        payload = self.PAYLOAD.copy()
        payload["planned_weight"] = Decimal("1" + "0" * max_length)
        payload["deposit"] = deposit_factory(budget=budget)
        payload["wallet"] = wallet_factory(budget=budget)

        with pytest.raises(ValidationError) as exc:
            WalletDeposit.objects.create(**payload)
        assert (
            exc.value.error_list[0].messages[0]
            == "Sum of planned weights for single Wallet cannot be greater than 100."
        )
        assert not WalletDeposit.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_value_too_low(
        self, budget: Budget, deposit_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit and Wallet models instances in database. Valid payload for WalletDeposit provided.
        WHEN: WalletDeposit instance create attempt with "value" value too low.
        THEN: DataError raised.
        """
        payload = self.PAYLOAD.copy()
        payload["planned_weight"] = Decimal("-0.01")
        payload["deposit"] = deposit_factory(budget=budget)
        payload["wallet"] = wallet_factory(budget=budget)

        with pytest.raises(IntegrityError) as exc:
            WalletDeposit.objects.create(**payload)

        assert 'violates check constraint "wallets_walletdeposit_planned_weight_gte_0"' in str(exc.value)
        assert not WalletDeposit.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_on_deposit_already_added_to_wallet(
        self, budget: Budget, deposit_factory: FactoryMetaClass, wallet_factory: FactoryMetaClass
    ):
        """
        GIVEN: Deposit and Wallet models instances in database. Valid payload for WalletDeposit provided.
        WHEN: Trying to create two WalletDeposit instances for the same deposit and wallet.
        THEN: IntegrityError raised.
        """
        deposit = deposit_factory(budget=budget)
        wallet = wallet_factory(budget=budget)
        WalletDeposit.objects.create(deposit=deposit, wallet=wallet, **self.PAYLOAD)

        with pytest.raises(IntegrityError) as exc:
            WalletDeposit.objects.create(deposit=deposit, wallet=wallet, **self.PAYLOAD)

        assert "duplicate key value violates unique constraint" in str(exc.value)
        assert WalletDeposit.objects.all().count() == 1

    @pytest.mark.django_db(transaction=True)
    def test_error_different_budgets_in_deposit_and_wallet(
        self,
        budget_factory: FactoryMetaClass,
        deposit_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Deposit and Wallet models instances in database. Valid payload for WalletDeposit provided.
        WHEN: Trying to create WalletDeposit with deposit and wallet from different budgets.
        THEN: ValidationError raised.
        """
        budget_1 = budget_factory()
        budget_2 = budget_factory()
        deposit = deposit_factory(budget=budget_1)
        wallet = wallet_factory(budget=budget_2)

        with pytest.raises(ValidationError) as exc:
            WalletDeposit.objects.create(deposit=deposit, wallet=wallet, **self.PAYLOAD)

        assert str(exc.value.args[0]) == "Budget not the same for Wallet and Deposit."
        assert not WalletDeposit.objects.all().exists()

    @pytest.mark.django_db(transaction=True)
    def test_error_planned_weight_sum_greater_than_100(
        self,
        budget: Budget,
        deposit_factory: FactoryMetaClass,
        wallet_factory: FactoryMetaClass,
        wallet_deposit_factory: FactoryMetaClass,
    ):
        """
        GIVEN: Two WalletDeposit instances for single Wallet in database.
        WHEN: Trying to create WalletDeposit, making summed planned_value exceeding 100.00.
        THEN: ValidationError raised.
        """
        wallet = wallet_factory(budget=budget)
        wallet_deposit_factory(wallet=wallet, deposit=deposit_factory(budget=budget), planned_weight=Decimal("40.00"))
        wallet_deposit_factory(wallet=wallet, deposit=deposit_factory(budget=budget), planned_weight=Decimal("40.00"))

        with pytest.raises(ValidationError) as exc:
            WalletDeposit.objects.create(
                deposit=deposit_factory(budget=budget), wallet=wallet, planned_weight=Decimal("20.01")
            )

        assert str(exc.value.args[0]) == "Sum of planned weights for single Wallet cannot be greater than 100."
        assert WalletDeposit.objects.filter(wallet=wallet).count() == 2
