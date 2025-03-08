from django.db import transaction
from django.db.models import QuerySet
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.filters import OrderingFilter
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from app_users.serializers.user_serializer import UserSerializer
from budgets.filtersets.budget_filterset import BudgetFilterSet
from budgets.models import Budget
from budgets.serializers.budget_serializer import BudgetSerializer


class BudgetViewSet(ModelViewSet):
    """View for manage Budgets."""

    serializer_class = BudgetSerializer
    queryset = Budget.objects.all()
    permission_classes = [IsAuthenticated]
    filterset_class = BudgetFilterSet
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter)
    ordering_fields = (
        "id",
        "name",
    )

    def get_queryset(self) -> QuerySet:
        """
        Retrieves Budgets membered by authenticated User.

        Returns:
            QuerySet: QuerySet containing Budgets containing authenticated User as member.
        """
        user = getattr(self.request, "user", None)
        if user and user.is_authenticated:
            return self.queryset.filter(members=user).order_by("id").distinct()
        return self.queryset.none()  # pragma: no cover

    @action(detail=True, methods=["GET"])
    def members(self, request: Request, **kwargs: dict) -> Response:
        """
        Endpoint returning members list of particular Budget.

        Args:
            request [Request]: User request.
            kwargs [dict]: Keyword arguments.

        Returns:
            Response: HTTP response with particular Budget members list.
        """
        budget = get_object_or_404(self.queryset.model, pk=kwargs.get("pk"))
        serializer = UserSerializer(budget.members.all(), many=True)
        return Response({"results": serializer.data})

    def perform_create(self, serializer: BudgetSerializer) -> None:
        """
        Adds request User as a member of Budget model.

        Args:
            serializer [BudgetSerializer]: Budget data serializer.
        """
        with transaction.atomic():
            budget = serializer.save()
            budget.members.add(self.request.user)
