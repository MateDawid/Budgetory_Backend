from pytest_factoryboy import register

from data_import.tests.factories import ImportFileFactory

register(ImportFileFactory, 'import_file_factory')
