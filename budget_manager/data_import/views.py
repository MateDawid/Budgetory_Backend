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
    def read_csv_file(csv_file: InMemoryUploadedFile) -> tuple[list, list]:
        """Returns tuple, containing file headers and file lines"""
        def get_headers(delimiter: str = ':') -> Union[list, Response]:
            """Returns headers. Retrieves headers from file lines if needed"""
            raw_headers = lines[0]
            # All headers provided, returning them
            if all(raw_headers):
                return raw_headers
            # Checking if data rows lengths the same as header length
            raw_headers_length = len(raw_headers)
            if not all([len(line) == raw_headers_length for line in lines]):
                return Response(
                    data={"error": "Headers length not the same as rows length"},
                    status=status.HTTP_409_CONFLICT
                )
            # Collecting missing headers
            processed_headers = []
            for line in lines[1:]:
                for cell_number, cell in enumerate(line):
                    original_header = raw_headers[cell_number]
                    if original_header:
                        if original_header not in processed_headers:
                            processed_headers.append(original_header)
                        continue
                    cell_parts = cell.split(delimiter)
                    if len(cell_parts) < 2:
                        continue
                    header = cell_parts[0].strip()
                    if header not in processed_headers:
                        processed_headers.append(header)
            return processed_headers

        def get_content() -> list:
            """Returns list of data dicts from csv lines"""
            return []

        read_file = csv_file.read()
        decoded_file = read_file.decode(encoding='utf-8', errors="replace")
        csv_source = StringIO(decoded_file)
        lines = [line for line in csv.reader(csv_source)]
        if not lines:
            return [], {}
        return get_headers(), get_content()

    def create(self, request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        csv_file = request.data['file']
        if not request.data.get('filename', ''):
            request.data['filename'] = csv_file.name
        headers, content = self.read_csv_file(csv_file)
        obj = serializer.save()
        obj.headers = headers
        obj.content = content
        obj.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
