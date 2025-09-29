from django.db import transaction
from rest_framework import generics
from rest_framework.response import Response

from app_users.serializers.user_register_serializer import UserRegisterSerializer
from app_users.utils import create_initial_categories_for_budget_pk
from budgets.models import Budget


class UserRegisterView(generics.CreateAPIView):
    """View to register new User."""

    serializer_class = UserRegisterSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs) -> Response:
        with transaction.atomic():
            response = self.create(request, *args, **kwargs)
            budget = Budget.objects.create(name="Your Budget", currency="$")
            budget.members.add(response.data.serializer.instance)
            create_initial_categories_for_budget_pk(budget_pk=budget.pk)
            return response
