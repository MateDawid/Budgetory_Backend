import pytest
from pytest_factoryboy import register

from data_import.tests.factories import ImportFileFactory

register(ImportFileFactory)


@pytest.fixture
def function_fixture():
    print('Fixture for each test')
    return 1