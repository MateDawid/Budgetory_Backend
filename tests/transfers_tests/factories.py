import random
from datetime import date

import factory.fuzzy
from budgets_tests.factories import BudgetFactory, BudgetingPeriodFactory
from categories_tests.factories import TransferCategoryFactory
from entities_tests.factories import DepositFactory, EntityFactory

from budgets.models import Budget, BudgetingPeriod
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit, Entity


class TransferFactory(factory.django.DjangoModelFactory):
    """Factory for Transfer model."""

    class Meta:
        model = "transfers.Transfer"

    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    value = factory.Faker("pyint", min_value=0, max_value=99999999)

    @factory.post_generation
    def budget(self, create: bool, budget: Budget, **kwargs) -> None:
        """
        Enables to pass "budget" as parameter to factory.

        Args:
            create [bool]: Indicates if object is created or updated.
            budget [Budget]: Budget model instance.
            **kwargs [dict]: Keyword arguments
        """
        pass

    @factory.lazy_attribute
    def period(self, *args) -> BudgetingPeriod:
        """
        Returns BudgetingPeriod with the same Budget as prediction category.

        Returns:
            BudgetingPeriod: BudgetingPeriod with the same Budget as category.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = BudgetFactory()
        return BudgetingPeriodFactory(budget=budget)

    @factory.lazy_attribute
    def entity(self, *args) -> Entity:
        """
        Returns Entity with the same Budget as prediction period.

        Returns:
            Entity: Entity with the same Budget as period.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.period.budget
        return EntityFactory(budget=budget)

    @factory.lazy_attribute
    def deposit(self, *args) -> Deposit:
        """
        Returns Deposit with the same Budget as prediction period.

        Returns:
            Deposit: Deposit with the same Budget as period.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.period.budget
        return DepositFactory(budget=budget)

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Budget as prediction period.

        Returns:
            TransferCategory: TransferCategory with the same Budget as period.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.period.budget
        return TransferCategoryFactory(budget=budget)

    @factory.lazy_attribute
    def date(self) -> date:
        """
        Generates date field basing on given period daterange.

        Returns:
            date: Generated Transfer date.
        """
        day = random.randint(self.period.date_start.day, self.period.date_end.day)
        return date(year=self.period.date_start.year, month=self.period.date_start.month, day=day)


class IncomeFactory(TransferFactory):
    """Factory for Income proxy model."""

    class Meta:
        model = "transfers.Income"

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Budget as prediction period and CategoryType.INCOME category_type value.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        payload = {
            "budget": self._Resolver__step.builder.extras.get("budget") or self.period.budget,
            "deposit": self._Resolver__step.builder.extras.get("deposit") or self.deposit,
        }
        return TransferCategoryFactory(category_type=CategoryType.INCOME, **payload)


class ExpenseFactory(TransferFactory):
    """Factory for Expense proxy model."""

    class Meta:
        model = "transfers.Expense"

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Budget as prediction period and CategoryType.EXPENSE category_type value.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        payload = {
            "budget": self._Resolver__step.builder.extras.get("budget") or self.period.budget,
            "deposit": self._Resolver__step.builder.extras.get("deposit") or self.deposit,
        }
        return TransferCategoryFactory(category_type=CategoryType.EXPENSE, **payload)
