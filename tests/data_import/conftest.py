import csv
import sys
from io import StringIO

import pytest
from django.core.files.uploadedfile import InMemoryUploadedFile
from pytest_factoryboy import register

from tests.data_import.factories import ImportFileFactory

register(ImportFileFactory)


@pytest.fixture
def valid_csv_file_content() -> list:
    data = [{'column_1': '1', 'column_2': '1'}, {'column_1': '1', 'column_2': '1'}]
    return data


@pytest.fixture
def valid_data_file(valid_csv_file_content) -> InMemoryUploadedFile:
    io_file = StringIO()
    writer = csv.DictWriter(io_file, fieldnames=valid_csv_file_content[0].keys())
    writer.writeheader()
    writer.writerows(valid_csv_file_content)
    io_file.seek(0)
    file = InMemoryUploadedFile(io_file, 'FileField', 'valid_file.csv', 'txt/csv', sys.getsizeof(io_file), None)
    return file


@pytest.fixture
def txt_file() -> InMemoryUploadedFile:
    io_file = StringIO()
    io_file.write('TEST TEXT')
    io_file.seek(0)
    file = InMemoryUploadedFile(io_file, 'FileField', 'text_file.txt', 'text/plain', sys.getsizeof(io_file), None)
    return file
