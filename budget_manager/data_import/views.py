import csv
from io import StringIO
from typing import Union

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import viewsets, status
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import ImportFile
from .serializers import ImportFileSerializer


class ImportFileViewSet(
    ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)
    queryset = ImportFile.objects.all()
    serializer_class = ImportFileSerializer

    @staticmethod
    def get_csv_data(csv_file: InMemoryUploadedFile, fixed_header_prefix: str = '__temp__') -> list:
        def get_fixed_headers() -> list:
            """Cleans headers from empty strings"""
            header_number = 1
            fixed_headers = []
            for header in reader.fieldnames:
                if not header:
                    fixed_headers.append(f'{fixed_header_prefix}{header_number}')
                    header_number += 1
                    continue
                fixed_headers.append(header)
            return fixed_headers

        def get_fixed_content() -> list:
            """Fill last valid key with data from empty columns"""
            reader.fieldnames = get_fixed_headers()
            last_valid_header = None
            for temp_header in reader.fieldnames[::-1]:
                if temp_header.startswith(fixed_header_prefix):
                    continue
                last_valid_header = temp_header
                break
            fixed_lines = []
            for line in reader:
                fixed_line = {}
                for key, value in line.items():
                    if key == last_valid_header:
                        value_parts = value.split(':')
                        fixed_line[last_valid_header] = {value_parts[0]: ':'.join(value_parts[1:]).strip()}
                        continue
                    if key.startswith(fixed_header_prefix):
                        value_parts = value.split(':')
                        fixed_line[last_valid_header][value_parts[0]] = ':'.join(value_parts[1:]).strip()
                        continue
                    fixed_line[key] = value
                fixed_line['id'] = str(fixed_line[last_valid_header])
                fixed_lines.append(fixed_line)
            return fixed_lines

        """Returns tuple, containing file headers and file lines"""
        read_file = csv_file.read()
        decoded_file = read_file.decode(encoding='utf-8', errors="replace")
        csv_source = StringIO(decoded_file)
        reader = csv.DictReader(csv_source)
        # All fieldnames provided
        if all(reader.fieldnames):
            return [line for line in reader]
        # Not all fieldnames provided
        lines = get_fixed_content()
        return lines

    @staticmethod
    def get_headers(csv_data: list) -> Union[list, Response]:
        """Returns csv file headers. Retrieves headers from file lines if needed"""
        return list(csv_data[0].keys())

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        csv_file = request.data['file']
        if not request.data.get('filename', ''):
            request.data['filename'] = csv_file.name
        csv_content = self.get_csv_data(csv_file)
        csv_headers = self.get_headers(csv_content)
        obj = serializer.save()
        obj.headers = csv_headers
        obj.content = csv_content
        obj.save()
        response_headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=response_headers)
