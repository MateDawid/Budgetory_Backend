import csv
import sys
from io import StringIO

import pytest
from data_import.tests.factories import ImportFileFactory
from django.core.files.uploadedfile import InMemoryUploadedFile
from pytest_factoryboy import register

register(ImportFileFactory)


@pytest.fixture
def valid_csv_file_content():
    data = [{'column_1': 1, 'column_2': 2}, {'column_1': 1, 'column_2': 2}]
    return data


@pytest.fixture
def valid_data_file(valid_csv_file_content):
    io_file = StringIO()
    writer = csv.DictWriter(io_file, fieldnames=valid_csv_file_content[0].keys())
    writer.writeheader()
    writer.writerows(valid_csv_file_content)
    io_file.seek(0)
    file = InMemoryUploadedFile(io_file, 'FileField', 'valid_file.csv', 'txt/csv', sys.getsizeof(io_file), None)
    return file
