import factory


class EntityFactory(factory.django.DjangoModelFactory):
    """Factory for Entity model."""

    class Meta:
        model = 'entities.Entity'

    name = factory.Faker('text', max_nb_chars=128)
    description = factory.Faker('text', max_nb_chars=255)
