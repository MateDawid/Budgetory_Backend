from django.contrib.auth import get_user_model
from rest_framework import authentication, generics, permissions

from .serializers import UserSerializer


class ListUserView(generics.ListAPIView):
    """View to list all users."""

    serializer_class = UserSerializer
    queryset = get_user_model().objects.all()
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAdminUser]


class CreateUserView(generics.CreateAPIView):
    """View to create a new user."""

    serializer_class = UserSerializer


class AuthenticatedUserView(generics.RetrieveUpdateAPIView):
    """View for managing authenticated user."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.BasicAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        """Retrieve and return the authenticated user."""
        return self.request.user
