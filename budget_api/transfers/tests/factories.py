import random

import factory.fuzzy
from app_users.tests.factories import UserFactory
from budgets.tests.factories import BudgetFactory
from transfers.managers import CategoryType
from transfers.models import TransferCategory


class TransferCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for TransferCategory model."""

    class Meta:
        model = 'transfers.TransferCategory'

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    is_active = factory.Faker('boolean')
    income_group = None
    expense_group = None

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)

    @factory.post_generation
    def category_type(self, create: bool, category_type: CategoryType, **kwargs) -> None:
        """
        Sets proper values for expense_group and income_group for indicated category_type.

        Args:
            create [bool]: Indicates if object is created or updated.
            category_type [CategoryType]: Type of TransferCategory.
            **kwargs [dict]: Keyword arguments
        """
        if not create:
            return
        expense_choices = [x[0] for x in TransferCategory.ExpenseGroups.choices]
        income_choices = [x[0] for x in TransferCategory.IncomeGroups.choices]

        if category_type == CategoryType.INCOME:
            self.income_group = random.choice(income_choices)
            self.expense_group = None
        elif category_type == CategoryType.EXPENSE:
            self.income_group = None
            self.expense_group = random.choice(expense_choices)
        else:
            self.income_group = random.choice(income_choices + len(income_choices) * [None])
            if self.income_group is None:
                self.expense_group = random.choice(expense_choices)
            else:
                self.expense_group = None
