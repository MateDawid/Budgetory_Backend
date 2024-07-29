from app_users.models import User
from app_users.serializers.user_serializer import UserSerializer
from rest_framework import authentication, generics, permissions


class AuthenticatedUserView(generics.RetrieveUpdateAPIView):
    """View for managing authenticated User."""

    serializer_class = UserSerializer
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> User | None:
        """
        Retrieves and returns the authenticated user.

        Returns:
            User | None: Authenticated User or None.
        """
        return self.request.user
