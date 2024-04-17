from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from transfers.models.transfer_category import TransferCategory
from transfers.permissions import IsPersonalTransferCategoryOwnerOrAdmin
from transfers.serializers import TransferCategorySerializer


class TransferCategoryViewSet(viewsets.ModelViewSet):
    """View for managing TransferCategories."""

    serializer_class = TransferCategorySerializer
    queryset = TransferCategory.objects.all()
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        """Checks permissions depending on view to execute."""
        if self.request.method == 'POST' and self.request.data.get('scope') == 'GLOBAL':
            return (IsAdminUser(),)
        if self.request.method in ['DELETE', 'PUT', 'PATCH']:
            return (IsPersonalTransferCategoryOwnerOrAdmin(),)
        return (IsAuthenticated(),)

    def get_queryset(self):
        """Retrieve global TransferCategories and personal TransferCategories for authenticated user."""
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return self.queryset.filter(
                Q(scope=TransferCategory.GLOBAL) | Q(scope=TransferCategory.PERSONAL, user=user)
            ).distinct()
        return self.queryset.none()  # pragma: no cover

    def create(self, request, *args, **kwargs):
        """Extend create method with passing user in serializer depending on TransferCategory type."""
        data = request.data.copy()
        match request.data.get('scope'):
            case TransferCategory.PERSONAL:
                data['user'] = request.user.id
            case _:
                data['user'] = None
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
