import factory
from app_users_tests.factories import UserFactory

from wallets.models import Currency


class WalletFactory(factory.django.DjangoModelFactory):
    """Factory for Wallet model."""

    class Meta:
        model = "wallets.Wallet"

    name = factory.Faker("text", max_nb_chars=128)
    description = factory.Faker("text", max_nb_chars=255)
    owner = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def currency(self) -> Currency:
        return Currency.objects.all().first()
