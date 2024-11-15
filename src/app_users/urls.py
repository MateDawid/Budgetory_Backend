from django.urls import path

from app_users.views.user_register_view import UserRegisterView

app_name = "app_users"

urlpatterns = [
    # path("", ListUserView.as_view(), name="list"),
    path("register/", UserRegisterView.as_view(), name="register"),
    # path("token/", CreateTokenView.as_view(), name="token"),
    # path("me/", AuthenticatedUserView.as_view(), name="me"),
]
