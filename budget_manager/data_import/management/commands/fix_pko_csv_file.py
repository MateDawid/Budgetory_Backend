import csv
import os
from copy import copy
from typing import BinaryIO, SupportsIndex

from django.core.management import BaseCommand, CommandError


class Decoder:
    MAPPING: dict = {
        '\\xa5': 'A',
        '\\xb9': 'a',
        '\\xc6': 'C',
        '\\xe6': 'c',
        '\\xca': 'E',
        '\\xb3': 'l',
        '\\xa3': 'L',
        '\\xd1': 'N',
        '\\xd3': 'O',
        '\\x8c': 'S',
        '\\x9c': 's',
        '\\x8f': 'Z',
        '\\xaf': 'Z',
    }

    def decode_file(self, binary_file: BinaryIO) -> list:
        return [self.get_decoded_line(line) for line in binary_file]

    def get_decoded_line(self, line: bytes) -> str:
        fixed_word = str(copy(line))[2:-5]
        for encoded_char in self.MAPPING:
            fixed_word = fixed_word.replace(encoded_char, self.MAPPING[encoded_char])
        return fixed_word


class Command(BaseCommand):
    """
    Corrects PKO .csv file to fit to data collection logic
    """

    help = 'Fixes PKO .csv file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to PKO .csv file')

    @staticmethod
    def is_file_path_valid(file_path: str) -> None:
        if not os.path.exists(file_path):
            raise CommandError('Provided string is not a path!')
        if not os.path.isfile(file_path):
            raise CommandError('Provided string is not a path to file!')
        if not file_path.endswith('.csv'):
            raise CommandError('Only .csv file allowed!')

    @staticmethod
    def is_reader_valid(reader: csv.DictReader) -> bool:
        if not all(reader.fieldnames):
            return False
        return True

    def get_fixed_content(self, reader: csv.DictReader, temp_header_prefix: str = '__temp__') -> list:
        def get_temporary_headers() -> list:
            """Cleans headers from empty strings"""
            header_number = 1
            fixed_headers = []
            for header in reader.fieldnames:
                if not header:
                    fixed_headers.append(f'{temp_header_prefix}{header_number}')
                    header_number += 1
                    continue
                fixed_headers.append(header)
            return fixed_headers

        def get_last_valid_header() -> SupportsIndex:
            return_header = None
            for temp_header in reader.fieldnames[::-1]:
                if temp_header.startswith(temp_header_prefix):
                    continue
                return_header = temp_header
                break
            return return_header

        def get_fixed_key_and_value() -> tuple:
            value_parts = value.split(':', maxsplit=1)
            return value_parts[0].strip(), value_parts[1].strip()

        """Fill last valid key with data from empty columns"""
        reader.fieldnames = get_temporary_headers()
        last_valid_header = get_last_valid_header()
        final_headers = set()
        final_lines = []
        for line in reader:
            tmp_line = {}
            for key, value in line.items():
                if key == last_valid_header:
                    fixed_key, fixed_value = get_fixed_key_and_value()
                    tmp_line[fixed_key] = fixed_value
                    final_headers.add(fixed_key)
                    continue
                if key.startswith(temp_header_prefix):
                    if value.startswith('Lokalizacja: '):
                        value = value.replace('Lokalizacja: ', '')
                        try:
                            location_data = {
                                'country': {
                                    'header': 'Kraj',
                                    'start_index': value.index('Kraj: '),
                                    'end_index': value.index('Miasto: '),
                                },
                                'city': {
                                    'header': 'Miasto',
                                    'start_index': value.index('Miasto: '),
                                    'end_index': value.index('Adres: '),
                                },
                                'address': {
                                    'header': 'Adres',
                                    'start_index': value.index('Adres: '),
                                },
                            }
                        except ValueError:
                            location_data = {
                                'address': {
                                    'header': 'Adres',
                                    'start_index': value.index('Adres: '),
                                },
                            }
                        for detail_data in location_data:
                            header, start_index, end_index = (
                                location_data[detail_data].get('header'),
                                location_data[detail_data].get('start_index'),
                                location_data[detail_data].get('end_index'),
                            )
                            if end_index:
                                tmp_line[header] = value[start_index:end_index].replace(f'{header}: ', '').strip()
                            else:
                                tmp_line[header] = value[start_index:].replace(f'{header}: ', '').strip()
                            final_headers.add(header)
                    else:
                        try:
                            fixed_key, fixed_value = get_fixed_key_and_value()
                        except IndexError:
                            continue
                        tmp_line[fixed_key] = fixed_value
                        final_headers.add(fixed_key)
                    continue
                tmp_line[key] = value
                final_headers.add(key)
            final_lines.append(tmp_line)
        # Add missing headers values for every line
        for final_line in final_lines:
            for final_header in final_headers:
                if final_header not in final_line:
                    final_line[final_header] = ''
        return final_lines

    def handle(self, *args, **options) -> None:
        decoder = Decoder()
        file_path = options['file_path']
        self.is_file_path_valid(file_path)
        self.stdout.write('FIXING STARTED')
        self.stdout.write('Processing invalid file')
        with open(file_path, 'rb') as binary_file:
            file = decoder.decode_file(binary_file)
            reader = csv.DictReader(file)
            lines = self.get_fixed_content(reader)
        file_directory = os.path.dirname(file_path)
        file_name = f'FIXED_{os.path.basename(file_path)[:-4]}.csv'
        new_file_path = os.path.join(file_directory, file_name)
        self.stdout.write(f'Saving file in path: {new_file_path}')
        with open(new_file_path, 'w') as new_file:
            writer = csv.DictWriter(new_file, lines[0].keys())
            writer.writeheader()
            writer.writerows(lines)
        self.stdout.write('FIXING ENDED')
