from app_config.permissions import UserBelongToBudgetPermission
from deposits.models import Deposit
from deposits.serializers import DepositSerializer
from django.db.models import Q
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class DepositViewSet(viewsets.ModelViewSet):
    """View for managing Deposits."""

    serializer_class = DepositSerializer
    queryset = Deposit.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, UserBelongToBudgetPermission]

    def get_queryset(self):
        """Retrieve Deposits for authenticated user."""
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            return self.queryset.filter(Q(budget__owner=user) | Q(budget__members=user)).distinct()
        return self.queryset.none()
