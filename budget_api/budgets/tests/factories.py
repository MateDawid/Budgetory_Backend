import datetime

import factory
from app_users.tests.factories import UserFactory
from django.contrib.auth.models import AbstractUser


class BudgetFactory(factory.django.DjangoModelFactory):
    """Factory for Budget model."""

    class Meta:
        model = 'budgets.Budget'

    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    currency = factory.Faker('text', max_nb_chars=3)
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def members(self, create: bool, users: list[AbstractUser], **kwargs) -> None:
        """
        Populates Budgets.members ManyToMany field with passed Users list.

        Args:
            create [bool]: Indicates if object is created or updated.
            users [list[AbstractUser]]:
            **kwargs [dict]: Keyword arguments
        """
        if not create or not users:
            return
        self.members.add(*users)


class BudgetingPeriodFactory(factory.django.DjangoModelFactory):
    """Factory for BudgetingPeriod model."""

    class Meta:
        model = 'budgets.BudgetingPeriod'

    user = factory.SubFactory(UserFactory)
    date_start = datetime.date(2023, 1, 1)
    date_end = datetime.date(2023, 1, 31)
    is_active = factory.Faker('boolean')

    @factory.lazy_attribute
    def name(self) -> str:
        """Generates period name basing on provided date_range."""
        year_start, year_end = self.date_start.year, self.date_end.year
        month_start, month_end = self.date_start.month, self.date_end.month
        if year_start == year_end and month_start == month_end:
            return f'{year_start}_{month_start:02d}'
        else:
            return f'{year_start}_{month_start:02d} - {year_end}_{month_end:02d}'  # pragma: no cover
