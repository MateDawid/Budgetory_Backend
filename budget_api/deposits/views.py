from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class DepositViewSet(viewsets.ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve Deposits for authenticated user."""
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return self.queryset.filter(user=user).distinct()
        return self.queryset.none()

    def perform_create(self, serializer):
        """Additionally save user in Deposit model."""
        serializer.save(user=self.request.user)
