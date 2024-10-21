import factory.fuzzy
from budgets_tests.factories import BudgetFactory


class WalletFactory(factory.django.DjangoModelFactory):
    """Factory for Wallet model."""

    class Meta:
        model = "wallets.Wallet"

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker("text", max_nb_chars=255)
