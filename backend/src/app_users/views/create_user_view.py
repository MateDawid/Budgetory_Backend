from rest_framework import generics

from app_users.serializers.user_serializer import UserSerializer


class CreateUserView(generics.CreateAPIView):
    """View to create a new User."""

    serializer_class = UserSerializer
    permission_classes = ()
