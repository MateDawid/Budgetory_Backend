from rest_framework import serializers

from .models import ImportFile


class ImportFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ImportFile
        fields = ['url', 'file', 'headers', 'content', 'filename', 'date_added']
        read_only_fields = ['filename', 'headers', 'content']
