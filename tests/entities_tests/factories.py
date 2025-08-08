import factory
from budgets_tests.factories import BudgetFactory

from entities.models.choices.deposit_type import DepositType


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory for Entity model."""

    class Meta:
        model = "entities.Entity"

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    is_active = factory.Faker("boolean")
    is_deposit = factory.LazyAttribute(lambda _: False)
    deposit_type = factory.LazyAttribute(lambda _: None)
    owner = factory.LazyAttribute(lambda _: None)


class DepositFactory(EntityFactory):
    """Factory for Deposit model."""

    is_deposit = factory.LazyAttribute(lambda _: True)
    deposit_type = factory.Iterator(DepositType.values)

    class Meta:
        model = "entities.Deposit"
