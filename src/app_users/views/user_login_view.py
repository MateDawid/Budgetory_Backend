from rest_framework_simplejwt.views import TokenObtainPairView

from app_users.serializers.user_login_serializer import UserLoginSerializer


class UserLoginView(TokenObtainPairView):
    serializer_class = UserLoginSerializer
