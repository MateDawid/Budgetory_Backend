from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from app_users.services.demo_login_service import get_demo_user_token


class DemoLoginView(APIView):
    """
    View for creating demo User and returning its credentials.
    """

    permission_classes = ()

    def post(self, request: Request) -> Response:
        if token := get_demo_user_token():
            return Response(token, status=status.HTTP_200_OK)
        return Response("Demo login failed.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
