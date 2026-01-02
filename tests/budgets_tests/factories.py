import random
import string

import factory
from app_users_tests.factories import UserFactory
from django.contrib.auth.models import AbstractUser


class BudgetFactory(factory.django.DjangoModelFactory):
    """Factory for Budget model."""

    class Meta:
        model = "budgets.Budget"

    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)

    @factory.lazy_attribute
    def currency(self) -> str:
        """Generates currency."""
        return "".join(random.choice(string.ascii_letters) for _ in range(3))

    @factory.post_generation
    def members(self, create: bool, users: list[AbstractUser], **kwargs) -> None:
        """
        Populates Budgets.members ManyToMany field with passed Users list.

        Args:
            create [bool]: Indicates if object is created or updated.
            users [list[AbstractUser]]:
            **kwargs [dict]: Keyword arguments
        """
        if not create:
            return
        if users:
            self.members.add(*users)
        else:
            self.members.add(UserFactory())
