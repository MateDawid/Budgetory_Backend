import factory
from budgets.models import BudgetingPeriod
from budgets.tests.factories import BudgetingPeriodFactory
from categories.models import ExpenseCategory
from categories.tests.factories import ExpenseCategoryFactory


class ExpensePredictionFactory(factory.django.DjangoModelFactory):
    """Factory for ExpensePrediction model."""

    class Meta:
        model = 'predictions.ExpensePrediction'

    value = factory.Faker('pyint', min_value=0, max_value=99999999)
    description = factory.Faker('text', max_nb_chars=255)

    @factory.lazy_attribute
    def period(self, *args) -> ExpenseCategory:
        """
        Returns ExpenseCategory with the same Budget as prediction period.

        Returns:
            ExpenseCategory: ExpenseCategory with the same Budget as period.
        """
        category = self._Resolver__step.builder.extras.get('category')
        if category:
            return BudgetingPeriodFactory(budget=self.category.budget)
        return BudgetingPeriodFactory()

    @factory.lazy_attribute
    def category(self, *args) -> BudgetingPeriod:
        """
        Returns BudgetingPeriod with the same Budget as prediction category.

        Returns:
            BudgetingPeriod: BudgetingPeriod with the same Budget as category.
        """
        period = self._Resolver__step.attributes.get('period')
        if period:
            return ExpenseCategoryFactory(budget=self.period.budget)
        return ExpenseCategoryFactory()
