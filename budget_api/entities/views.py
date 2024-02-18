from django.db.models import Q
from entities.models import Entity
from entities.permissions import IsPersonalEntityOwnerOrAdmin
from entities.serializers import EntitySerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


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
        return self.queryset.filter(Q(type='GLOBAL') | Q(type='PERSONAL', user=self.request.user)).distinct()

    def create(self, request, *args, **kwargs):
        """Extend create method with passing user in serializer depending on Entity type."""
        match request.data.get('type'):
            case 'PERSONAL':
                request.data['user'] = request.user.id
            case 'GLOBAL':
                request.data['user'] = None
        return super().create(request, *args, **kwargs)
