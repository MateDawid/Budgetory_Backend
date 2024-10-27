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

    wallet = factory.SubFactory(WalletFactory)
    deposit = factory.SubFactory(DepositFactory)
    planned_weight = factory.Faker("pyint", min_value=0, max_value=100)

    @factory.lazy_attribute
    def wallet(self, *args) -> Wallet:
        """
        Returns BudgetingPeriod with the same Budget as prediction category.

        Returns:
            BudgetingPeriod: BudgetingPeriod with the same Budget as category.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = BudgetFactory()
        return WalletFactory(budget=budget)

    @factory.lazy_attribute
    def deposit(self, *args) -> Deposit:
        """
        Returns ExpenseCategory with the same Budget as prediction period.

        Returns:
            ExpenseCategory: ExpenseCategory with the same Budget as period.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.wallet.budget
        return DepositFactory(budget=budget)

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
