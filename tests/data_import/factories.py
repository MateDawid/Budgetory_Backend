import factory
from data_import.models import ImportFile


class ImportFileFactory(factory.django.DjangoModelFactory):
    date_added = factory.Faker('date_time_between', start_date='-1y', end_date='now')

    class Meta:
        model = ImportFile
