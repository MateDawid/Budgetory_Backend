import csv
import sys
from io import StringIO

import pytest
from data_import.tests.factories import ImportFileFactory
from django.core.files.uploadedfile import InMemoryUploadedFile
from pytest_factoryboy import register

register(ImportFileFactory)


@pytest.fixture
def valid_file_content() -> list:
    data = [{'column_1': '1', 'column_2': '1'}, {'column_1': '1', 'column_2': '1'}]
    return data


@pytest.fixture
def valid_data_file(valid_file_content: list) -> InMemoryUploadedFile:
    io_file = StringIO()
    writer = csv.DictWriter(io_file, fieldnames=valid_file_content[0].keys())
    writer.writeheader()
    writer.writerows(valid_file_content)
    io_file.seek(0)
    file = InMemoryUploadedFile(io_file, 'FileField', 'valid_file.csv', 'txt/csv', sys.getsizeof(io_file), None)
    return file


@pytest.fixture
def invalid_headers_file_content() -> list:
    data = [{'column_1': '1', 'column_2': '1', '': 'INVALID'}, {'column_1': '1', 'column_2': '1', '': 'INVALID'}]
    return data


@pytest.fixture
def invalid_headers_data_file(invalid_headers_file_content: list) -> InMemoryUploadedFile:
    io_file = StringIO()
    writer = csv.DictWriter(io_file, fieldnames=invalid_headers_file_content[0].keys())
    writer.writeheader()
    writer.writerows(invalid_headers_file_content)
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
