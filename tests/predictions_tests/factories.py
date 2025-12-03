import factory
from budgets_tests.factories import BudgetFactory, BudgetingPeriodFactory
from categories_tests.factories import TransferCategoryFactory
from entities_tests.factories import DepositFactory

from budgets.models import Budget, BudgetingPeriod
from budgets.models.choices.period_status import PeriodStatus
from categories.models import TransferCategory
from categories.models.choices.category_type import CategoryType
from entities.models import Deposit


class ExpensePredictionFactory(factory.django.DjangoModelFactory):
    """Factory for ExpensePrediction model."""

    class Meta:
        model = "predictions.ExpensePrediction"

    current_plan = factory.Faker("pyint", min_value=0, max_value=99999999)
    description = factory.Faker("text", max_nb_chars=255)

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
    def deposit(self, *args) -> Deposit:
        """
        Returns Deposit with the same Budget as prediction period.

        Returns:
            Deposit: Deposit with the same Budget as period.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.period.budget
        if category := self._Resolver__step.builder.extras.get("category"):
            return category.deposit
        return DepositFactory(budget=budget)

    @factory.lazy_attribute
    def initial_plan(self, *args) -> float | None:
        """
        Returns TransferCategory with the same Budget as prediction period and CategoryType.EXPENSE category_type field.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        if self.period.status in (PeriodStatus.ACTIVE, PeriodStatus.CLOSED):
            return self.current_plan
        else:
            return None

    @factory.lazy_attribute
    def category(self, *args) -> TransferCategory:
        """
        Returns TransferCategory with the same Budget as prediction period and CategoryType.EXPENSE category_type field.

        Returns:
            TransferCategory: Generated TransferCategory.
        """
        budget = self._Resolver__step.builder.extras.get("budget")
        if not budget:
            budget = self.period.budget
        return TransferCategoryFactory(
            budget=budget, deposit=self._Resolver__step.attributes.get("deposit"), category_type=CategoryType.EXPENSE
        )

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
