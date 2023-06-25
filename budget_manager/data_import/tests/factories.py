import factory

from data_import.models import ImportFile


class ImportFileFactory(factory.django.DjangoModelFactory):
    file = factory.Faker('file')
    filename = factory.Faker('word')
    headers = factory.Faker('pylist')
    content = factory.Faker('pydict')
    date_added = factory.Faker('date_time_between', start_date="-30y", end_date="now", tzinfo=pytz.UTC)

    class Meta:
        model = ImportFile
