import random

import factory.fuzzy
from app_users_tests.factories import UserFactory
from budgets_tests.factories import BudgetFactory
from categories.models import ExpenseCategory, IncomeCategory
from categories.models.category_priority_choices import CategoryPriority
from categories.models.category_type_choices import CategoryType


class TransferCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for TransferCategory model."""

    class Meta:
        model = "categories.TransferCategory"

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    is_active = factory.Faker("boolean")

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)

    @factory.lazy_attribute
    def category_type(self, *args) -> CategoryType:
        """
        Returns CategoryType matching priority value.

        Returns:
            CategoryType: Category type choice matching selected priority value.
        """
        priority = self._Resolver__step.builder.extras.get("priority")
        if priority is None:
            category_type = random.choice([choice for choice in CategoryType])
        elif priority == CategoryPriority.INCOMES:
            category_type = CategoryType.INCOME
        else:
            category_type = CategoryType.EXPENSE
        self._Resolver__step.builder.extras["category_type"] = category_type
        return category_type

    @factory.lazy_attribute
    def priority(self, *args) -> CategoryPriority:
        """
        Returns CategoryPriority matching category_type.

        Returns:
            CategoryPriority: Category priority choice matching selected category_type.
        """
        category_type = self._Resolver__step.builder.extras.get("category_type")
        if category_type is None:
            priority = random.choice([choice for choice in CategoryType])
        elif category_type == CategoryType.INCOME:
            priority = CategoryPriority.INCOMES
        else:
            priority = random.choice([choice for choice in CategoryPriority if choice != CategoryPriority.INCOMES])
        self._Resolver__step.builder.extras["priority"] = priority
        return priority


class IncomeCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for IncomeCategory model."""

    class Meta:
        model = "categories.IncomeCategory"

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    is_active = factory.Faker("boolean")
    group = factory.fuzzy.FuzzyChoice([x[0] for x in IncomeCategory.IncomeGroups.choices])

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)


class ExpenseCategoryFactory(factory.django.DjangoModelFactory):
    """Factory for ExpenseCategory model."""

    class Meta:
        model = "categories.ExpenseCategory"

    budget = factory.SubFactory(BudgetFactory)
    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    is_active = factory.Faker("boolean")
    group = factory.fuzzy.FuzzyChoice([x[0] for x in ExpenseCategory.ExpenseGroups.choices])

    @factory.lazy_attribute
    def owner(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)
