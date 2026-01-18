from rest_framework import generics

from app_users.serializers.user_register_serializer import UserRegisterSerializer


class UserRegisterView(generics.CreateAPIView):
    """View to register new User."""

    serializer_class = UserRegisterSerializer
    permission_classes = ()
