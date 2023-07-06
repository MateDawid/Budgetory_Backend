import csv
import os
from typing import SupportsIndex

from django.core.management import BaseCommand, CommandError

SIGNS_MAPPING = {

}


class Command(BaseCommand):
    """
    Corrects PKO .csv file to fit to data collection logic
    """
    help = "Fixes PKO .csv file"

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to PKO .csv file')

    @staticmethod
    def is_file_path_valid(file_path: str) -> None:
        if not os.path.exists(file_path):
            raise CommandError(f'Provided string is not a path!')
        if not os.path.isfile(file_path):
            raise CommandError(f'Provided string is not a path to file!')
        if not file_path.endswith('.csv'):
            raise CommandError(f'Only .csv file allowed!')

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
            value_parts = value.split(':')
            fixed_key = value_parts[0].strip()
            fixed_value = ':'.join(value_parts[1:]).strip()
            return fixed_key, fixed_value

        """Fill last valid key with data from empty columns"""
        reader.fieldnames = get_temporary_headers()
        last_valid_header = get_last_valid_header()
        final_headers = []
        final_lines = []
        for line in reader:
            tmp_line = {'id': []}
            for key, value in line.items():
                if key.startswith(temp_header_prefix) or key == last_valid_header:
                    new_key, new_value = get_fixed_key_and_value()
                    if new_key:
                        tmp_line[new_key] = new_value
                        tmp_line['id'].append(new_value)
                        if new_key not in final_headers:
                            final_headers.append(new_key)
                    continue
                tmp_line[key] = value
                if key and key not in final_headers:
                    final_headers.append(key)
            tmp_line['id'] = '|'.join(tmp_line['id'])
            final_lines.append(tmp_line)
        for final_line in final_lines:
            for final_header in final_headers:
                if final_header not in final_line:
                    final_line[final_header] = ''
        return final_lines

    def handle(self, *args, **options) -> None:
        file_path = options['file_path']
        self.is_file_path_valid(file_path)
        self.stdout.write('FIXING STARTED')
        self.stdout.write('Processing invalid file')
        with open(file_path, 'r') as file:
            reader = csv.DictReader(file)
            lines = self.get_fixed_content(reader)
        file_directory = os.path.dirname(file_path)
        file_name = f'{os.path.basename(file_path)[:-4]}_fixed.csv'
        new_file_path = os.path.join(file_directory, file_name)
        self.stdout.write(f'Saving file in path: {new_file_path}')
        with open(new_file_path, 'w') as new_file:
            writer = csv.DictWriter(new_file, lines[0].keys())
            writer.writeheader()
            writer.writerows(lines)
        self.stdout.write('FIXING ENDED')
