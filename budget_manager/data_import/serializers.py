from rest_framework import serializers

from .models import ImportFile


class ImportFileSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ImportFile
        fields = ['url', 'file', 'filename', 'date_added']
