from rest_framework import viewsets
from rest_framework.mixins import (
    CreateModelMixin,
    DestroyModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.permissions import IsAuthenticated

from .models import ImportFile
from .serializers import ImportFileSerializer


class ImportFileViewSet(
    ListModelMixin, CreateModelMixin, RetrieveModelMixin, DestroyModelMixin, UpdateModelMixin, viewsets.GenericViewSet
):
    permission_classes = (IsAuthenticated,)
    queryset = ImportFile.objects.all()
    serializer_class = ImportFileSerializer
