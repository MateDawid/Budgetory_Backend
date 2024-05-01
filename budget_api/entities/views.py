from django.db.models import Q
from entities.models import Entity
from entities.permissions import IsPersonalEntityOwnerOrAdmin
from entities.serializers import EntitySerializer
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class EntityViewSet(viewsets.ModelViewSet):
    """View for managing Entities."""

    serializer_class = EntitySerializer
    queryset = Entity.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        """Checks permissions depending on view to execute."""
        if self.request.method in ['DELETE', 'PUT', 'PATCH']:
            return (IsPersonalEntityOwnerOrAdmin(),)
        return (IsAuthenticated(),)

    def get_queryset(self):
        """Retrieve global Entities and personal Entities for authenticated user."""
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return self.queryset.filter(Q(type='GLOBAL') | Q(type='PERSONAL', user=user)).distinct()
        return self.queryset.none()  # pragma: no cover

    def create(self, request, *args, **kwargs):
        """Extend create method with passing user in serializer depending on Entity type."""
        data = request.data.copy()
        match request.data.get('type'):
            case Entity.PERSONAL:
                data['user'] = request.user.id
            case _:
                data['user'] = None
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
