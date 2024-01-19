import factory
from app_users.tests.factories import UserFactory


class DepositFactory(factory.django.DjangoModelFactory):
    """Factory for Deposit model."""

    class Meta:
        model = 'deposits.Deposit'

    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
    user = factory.SubFactory(UserFactory)
    is_active = factory.Faker('boolean')
