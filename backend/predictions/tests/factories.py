import factory
from budgets.tests.factories import BudgetingPeriodFactory
from categories.tests.factories import ExpenseCategoryFactory


class ExpensePredictionFactory(factory.django.DjangoModelFactory):
    """Factory for ExpensePrediction model."""

    class Meta:
        model = 'predictions.ExpensePrediction'

    period = factory.SubFactory(BudgetingPeriodFactory)
    category = factory.SubFactory(ExpenseCategoryFactory)
    value = factory.Faker('pyint', min_value=0, max_value=99999999)
    description = factory.Faker('text', max_nb_chars=255)
