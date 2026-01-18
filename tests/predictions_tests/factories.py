import factory
from categories_tests.factories import TransferCategoryFactory
from entities_tests.factories import DepositFactory
from periods_tests.factories import PeriodFactory
from wallets_tests.factories import WalletFactory

from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit
from periods.models import Period
from periods.models.choices.period_status import PeriodStatus
from wallets.models import Wallet


class ExpensePredictionFactory(factory.django.DjangoModelFactory):
    """Factory for ExpensePrediction model."""

    class Meta:
        model = "predictions.ExpensePrediction"

    current_plan = factory.Faker("pyint", min_value=0, max_value=99999999)
    description = factory.Faker("text", max_nb_chars=255)

    @factory.lazy_attribute
    def period(self, *args) -> Period:
        """
        Returns Period with the same Wallet as prediction category.

        Returns:
            Period: Period with the same Wallet as category.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = WalletFactory()
        return PeriodFactory(wallet=wallet)

    @factory.lazy_attribute
    def deposit(self, *args) -> Deposit:
        """
        Returns Deposit with the same Wallet as prediction period.

        Returns:
            Deposit: Deposit with the same Wallet as period.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = self.period.wallet
        category = self._Resolver__step.builder.extras.get("category")
        if isinstance(category, TransferCategory):
            return category.deposit
        return DepositFactory(wallet=wallet)

    @factory.lazy_attribute
    def initial_plan(self, *args) -> float | None:
        """
        Returns TransferCategory with the same Wallet as prediction period and CategoryType.EXPENSE category_type field.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        if self.period.status in (PeriodStatus.ACTIVE, PeriodStatus.CLOSED):
            return self.current_plan
        else:
            return None

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Wallet as prediction period and CategoryType.EXPENSE category_type field.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        wallet = self._Resolver__step.builder.extras.get("wallet")
        if not wallet:
            wallet = self.period.wallet
        return TransferCategoryFactory(
            wallet=wallet, deposit=self._Resolver__step.attributes.get("deposit"), category_type=CategoryType.EXPENSE
        )

    @factory.post_generation
    def wallet(self, create: bool, wallet: Wallet, **kwargs) -> None:
        """
        Enables to pass "wallet" as parameter to factory.

        Args:
            create [bool]: Indicates if object is created or updated.
            wallet [Wallet]: Wallet model instance.
            **kwargs [dict]: Keyword arguments
        """
        pass
