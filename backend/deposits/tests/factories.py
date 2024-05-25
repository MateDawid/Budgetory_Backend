import factory.fuzzy
from budgets.tests.factories import BudgetFactory
from deposits.models import Deposit


class DepositFactory(factory.django.DjangoModelFactory):
    """Factory for Deposit model."""

    class Meta:
        model = 'deposits.Deposit'

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    deposit_type = factory.fuzzy.FuzzyChoice([x[0] for x in Deposit.DepositTypes.choices])
    is_active = factory.Faker('boolean')
