import random

import factory.fuzzy
from app_users.tests.factories import UserFactory
from budgets.tests.factories import BudgetFactory
from transfers.models.transfer_category_group_model import TransferCategoryGroup


class TransferCategoryGroupFactory(factory.django.DjangoModelFactory):
    """Factory for TransferCategoryGroup model."""

    class Meta:
        model = 'transfers.TransferCategoryGroup'

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    transfer_type = factory.fuzzy.FuzzyChoice([x[0] for x in TransferCategoryGroup.TransferTypes.choices])


class TransferCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for TransferCategory model."""

    class Meta:
        model = 'transfers.TransferCategory'

    group = factory.SubFactory(TransferCategoryGroupFactory)
    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    is_active = factory.Faker('boolean')

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)
