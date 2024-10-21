import factory.fuzzy
from entities_tests.factories import DepositFactory
from wallets_tests.factories.wallet_factory import WalletFactory


class WalletDepositFactory(factory.django.DjangoModelFactory):
    """Factory for WalletDeposit model."""

    class Meta:
        model = "wallets.WalletDeposit"

    wallet = factory.SubFactory(WalletFactory)
    deposit = factory.SubFactory(DepositFactory)
    planned_weight = factory.Faker("pyint", min_value=0, max_value=100)
