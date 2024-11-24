from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from app_users.views.user_login_view import UserLoginView
from app_users.views.user_register_view import UserRegisterView

app_name = "app_users"

urlpatterns = [
    path("register/", UserRegisterView.as_view(), name="register"),
    path("login/", UserLoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
