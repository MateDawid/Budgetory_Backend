from django.db import transaction
from rest_framework import generics, status
from rest_framework.response import Response

from app_users.serializers.user_register_serializer import UserRegisterSerializer
from budgets.models import Budget


class UserRegisterView(generics.CreateAPIView):
    """View to register new User."""

    serializer_class = UserRegisterSerializer
    permission_classes = ()

    def post(self, request, *args, **kwargs) -> Response:
        try:
            with transaction.atomic():
                response = self.create(request, *args, **kwargs)
                budget = Budget.objects.create(name="Your Budget", currency="$")
                budget.members.add(response.data.serializer.instance)
        except Exception:
            response = Response("User creation failed.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return response
