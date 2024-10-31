import random
from decimal import Decimal

import factory.fuzzy
from budgets_tests.factories import BudgetFactory
from entities_tests.factories import DepositFactory
from wallets_tests.factories.wallet_factory import WalletFactory

from budgets.models import Budget
from entities.models import Deposit
from wallets.models import Wallet


class WalletDepositFactory(factory.django.DjangoModelFactory):
    """Factory for WalletDeposit model."""

    class Meta:
        model = "wallets.WalletDeposit"

    @factory.lazy_attribute
    def wallet(self, *args) -> Wallet:
        """
        Returns Wallet with the same Budget as deposit.

        Returns:
            Wallet: Wallet with the same Budget as deposit.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = BudgetFactory()
        return WalletFactory(budget=budget)

    @factory.lazy_attribute
    def deposit(self, *args) -> Deposit:
        """
        Returns Deposit with the same Budget as wallet.

        Returns:
            Deposit: Deposit with the same Budget as wallet.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.wallet.budget
        return DepositFactory(budget=budget)

    @factory.lazy_attribute
    def planned_weight(self, *args) -> Decimal:
        """
        Returns calculated planned_weight for WalletDeposit.

        Returns:
            Decimal: Calculated planned_weight for WalletDeposit.
        """
        wallet_weights_sum = Decimal(sum(self.wallet.deposits.values_list("planned_weight", flat=True)))
        available_range_max = int(Decimal("100.00") - wallet_weights_sum)
        choice = random.randrange(0, int(available_range_max))
        return Decimal(choice).quantize(Decimal(".01"))

    @factory.post_generation
    def budget(self, create: bool, budget: Budget, **kwargs) -> None:
        """
        Enables to pass "budget" as parameter to factory.

        Args:
            create [bool]: Indicates if object is created or updated.
            budget [Budget]: Budget model instance.
            **kwargs [dict]: Keyword arguments
        """
        pass
