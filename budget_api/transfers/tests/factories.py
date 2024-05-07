import random

import factory.fuzzy
from app_users.tests.factories import UserFactory
from budgets.tests.factories import BudgetFactory
from transfers.models import TransferCategory


class TransferCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for TransferCategory model."""

    class Meta:
        model = 'transfers.TransferCategory'

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    is_active = factory.Faker('boolean')
    expense_group = factory.fuzzy.FuzzyChoice([x[0] for x in TransferCategory.ExpenseGroups.choices])
    income_group = factory.fuzzy.FuzzyChoice([x[0] for x in TransferCategory.IncomeGroups.choices])

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)
