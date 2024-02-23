import random

import factory
from app_users.tests.factories import UserFactory
from entities.models import Entity


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory for Entity model."""

    class Meta:
        model = 'entities.Entity'

    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)

    @factory.lazy_attribute
    def user(self) -> str:
        """Generates user field value - User model instance or None."""
        options = [UserFactory(), None]
        return random.choice(options)

    @factory.lazy_attribute
    def type(self) -> str:
        """Generates type field value basing on user field value."""
        if self.user is None:
            return Entity.GLOBAL
        else:
            return Entity.PERSONAL
