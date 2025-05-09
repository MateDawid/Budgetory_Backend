import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model."""

    class Meta:
        model = get_user_model()

    email = factory.Faker("email")
    username = factory.Faker("user_name")
