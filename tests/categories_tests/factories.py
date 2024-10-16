import random

import factory.fuzzy
from app_users_tests.factories import UserFactory
from budgets_tests.factories import BudgetFactory

from categories.models.transfer_category_choices import CategoryType, ExpenseCategoryPriority, IncomeCategoryPriority


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
        if priority in IncomeCategoryPriority:
            category_type = CategoryType.INCOME
        elif priority in ExpenseCategoryPriority:
            category_type = CategoryType.EXPENSE
        else:
            category_type = random.choice([choice for choice in CategoryType])
        self._Resolver__step.builder.extras["category_type"] = category_type
        return category_type

    @factory.lazy_attribute
    def priority(self, *args) -> IncomeCategoryPriority | ExpenseCategoryPriority:
        """
        Returns CategoryPriority matching category_type.

        Returns:
            CategoryPriority: Category priority choice matching selected category_type.
        """
        category_type = self._Resolver__step.builder.extras.get("category_type")
        if category_type == CategoryType.INCOME:
            priority = random.choice([choice for choice in IncomeCategoryPriority])
        elif category_type == CategoryType.EXPENSE:
            priority = random.choice([choice for choice in ExpenseCategoryPriority])
        else:
            priority_type = random.choice([ExpenseCategoryPriority, IncomeCategoryPriority])
            priority = random.choice([choice for choice in priority_type])
        self._Resolver__step.builder.extras["priority"] = priority
        return priority


class IncomeCategoryFactory(TransferCategoryFactory):
    """Factory for IncomeCategory proxy model."""

    category_type = factory.LazyAttribute(lambda _: CategoryType.INCOME)
    priority = factory.fuzzy.FuzzyChoice([choice for choice in IncomeCategoryPriority])

    class Meta:
        model = "categories.TransferCategory"


class ExpenseCategoryFactory(TransferCategoryFactory):
    """Factory for IncomeCategory proxy model."""

    category_type = factory.LazyAttribute(lambda _: CategoryType.EXPENSE)
    priority = factory.fuzzy.FuzzyChoice([choice for choice in ExpenseCategoryPriority])

    class Meta:
        model = "categories.TransferCategory"
