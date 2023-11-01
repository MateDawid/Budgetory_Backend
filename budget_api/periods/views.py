from django.core.exceptions import ValidationError as DjangoValidationError
from periods.models import BudgetingPeriod
from periods.serializers import BudgetingPeriodSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import ValidationError as DRFValidationError
from rest_framework.permissions import IsAuthenticated


class BudgetingPeriodViewSet(viewsets.ModelViewSet):
    """View for manage BudgetingPeriods."""

    serializer_class = BudgetingPeriodSerializer
    queryset = BudgetingPeriod.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Retrieve BudgetingPeriods for authenticated user."""
        return self.queryset.filter(user=self.request.user).order_by('-date_start').distinct()

    def perform_create(self, serializer):
        """Create BudgetingPeriod in database or return model error."""
        try:
            serializer.save(user=self.request.user)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message)
