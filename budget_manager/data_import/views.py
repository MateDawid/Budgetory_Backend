from rest_framework import viewsets, status
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
)
from rest_framework.parsers import MultiPartParser, JSONParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import ImportFile
from .serializers import ImportFileSerializer


class ImportFileViewSet(
    ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)
    queryset = ImportFile.objects.all()
    serializer_class = ImportFileSerializer

    def get_parsers(self) -> [JSONParser | MultiPartParser | FormParser]:
        if 'POST' in str(self.request):
            return [MultiPartParser()]
        return super().get_parsers()
