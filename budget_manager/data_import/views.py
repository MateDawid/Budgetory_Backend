import csv
from io import StringIO

import rest_framework.request
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
    def get_csv_reader(csv_file: InMemoryUploadedFile) -> csv.DictReader:
        """Returns tuple, containing file headers and file lines"""
        read_file = csv_file.read()
        decoded_file = read_file.decode(encoding='utf-8', errors="replace")
        csv_source = StringIO(decoded_file)
        return csv.DictReader(csv_source)

    @staticmethod
    def validate_csv_file(csv_file: csv.DictReader) -> list:
        """Returns list of errors found in csv file"""
        errors = []
        if not all(csv_file.fieldnames):
            errors.append('Not all headers provided.')
        return errors

    @staticmethod
    def get_headers(csv_data: list) -> list:
        """Returns csv file headers. Retrieves headers from file lines if needed"""
        return list(csv_data[0].keys())

    def create(self, request: rest_framework.request.Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        csv_file = request.data['file']
        request.data['filename'] = csv_file.name
        csv_reader = self.get_csv_reader(csv_file)
        validation_errors = self.validate_csv_file(csv_reader)
        if validation_errors:
            return Response({'errors': validation_errors}, status=status.HTTP_406_NOT_ACCEPTABLE)
        csv_content = [line for line in csv_reader]
        csv_headers = self.get_headers(csv_content)
        obj = serializer.save()
        obj.headers = csv_headers
        obj.content = csv_content
        obj.save()
        response_headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=response_headers)
