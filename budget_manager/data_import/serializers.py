import csv
from io import StringIO
from typing import Any, Sequence

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework import serializers

from .models import ImportFile


class ImportFileSerializer(serializers.HyperlinkedModelSerializer):
    file = serializers.FileField(required=True, write_only=True)
    filename = serializers.CharField(required=False)
    __headers = None
    __content = None

    class Meta:
        model = ImportFile
        fields = ['url', 'file', 'headers', 'content', 'filename', 'date_added']
        read_only_fields = ['filename', 'headers', 'content']

    def validate_file(self, value: InMemoryUploadedFile) -> InMemoryUploadedFile | serializers.ValidationError:
        # File extension - it has to be .csv
        extension = value.name.rsplit('.', 1)[1].lower()
        if extension != 'csv':
            raise serializers.ValidationError(f'Only .csv files are allowed - .{extension} is not valid extension.')
        # All file headers should be non-empty string
        headers, _ = self.get_csv_content(value)
        if not all(headers):
            raise serializers.ValidationError('Not all headers provided in .csv file.')
        return value

    def get_csv_content(self, csv_file: InMemoryUploadedFile) -> tuple[Sequence[str] | None, list[Any]]:
        """Returns tuple, containing file headers and file lines store in protected attributes"""
        if self.__headers is not None and self.__content is not None:
            return self.__headers, self.__content
        read_file = csv_file.read()
        decoded_file = read_file.decode(encoding='utf-8', errors="replace")
        csv_source = StringIO(decoded_file)
        reader = csv.DictReader(csv_source)
        self.__headers = reader.fieldnames
        self.__content = list(reader)
        return self.__headers, self.__content

    def create(self, validated_data: dict) -> ImportFile:
        csv_file = validated_data.pop('file')
        if 'filename' not in validated_data:
            validated_data['filename'] = csv_file.name
        validated_data['headers'], validated_data['content'] = self.get_csv_content(csv_file)
        import_file = ImportFile.objects.create(**validated_data)
        return import_file
